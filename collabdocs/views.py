
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import (
    AuditLog,
    Comment,
    Document,
    DocumentVersion,
    Tag,
    User,
    Workspace,
    WorkspaceMember,
)
from .serializers import (
    AuditLogSerializer,
    CommentSerializer,
    DocumentSerializer,
    DocumentVersionSerializer,
    TagSerializer,
    UserSerializer,
    WorkspaceMemberSerializer,
    WorkspaceSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ["get", "post", "head", "options"]


class WorkspaceViewSet(viewsets.ModelViewSet):
    serializer_class = WorkspaceSerializer

    def get_queryset(self):
        return (
            Workspace.objects.select_related("owner")
            .prefetch_related("members__user")
            .annotate(member_count=Count("members", distinct=True))
        )

    def perform_create(self, serializer):
        # Workspace and owner membership must succeed or fail together.
        with transaction.atomic():
            workspace = serializer.save()
            WorkspaceMember.objects.create(
                workspace=workspace,
                user=workspace.owner,
                role=WorkspaceMember.Role.ADMIN,
            )

    @action(detail=True, methods=["get", "post"], url_path="members")
    def members(self, request, pk=None):
        workspace = self.get_object()

        if request.method == "GET":
            members = workspace.members.select_related("user").all()
            serializer = WorkspaceMemberSerializer(
                members, many=True, context=self.get_serializer_context()
            )
            return Response(serializer.data)

        serializer = WorkspaceMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                member = WorkspaceMember.objects.create(
                    workspace=workspace,
                    **serializer.validated_data,
                )
        except IntegrityError:
            return Response(
                {"detail": "This user is already a member of this workspace."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            WorkspaceMemberSerializer(member).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="summary")
    def summary(self, request, pk=None):
        workspace = self.get_object()

        counts = Workspace.objects.filter(pk=workspace.pk).aggregate(
            document_count=Count("documents", distinct=True),
            member_count=Count("members", distinct=True),
            total_comments=Count("documents__comments", distinct=True),
        )

        return Response(counts)


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer

    def get_queryset(self):
        queryset = (
            Document.objects.select_related("workspace", "created_by")
            .prefetch_related("versions", "tags", "comments")
            .annotate(
                version_count=Count("versions", distinct=True),
                comment_count=Count("comments", distinct=True),
            )
        )

        workspace_id = self.request.query_params.get("workspace")
        document_status = self.request.query_params.get("status")
        tag_name = self.request.query_params.get("tag")
        search_term = self.request.query_params.get("search")

        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)

        if document_status:
            queryset = queryset.filter(status=document_status)

        if tag_name:
            queryset = queryset.filter(tags__name__iexact=tag_name)

        if search_term:
            queryset = queryset.filter(
                Q(title__icontains=search_term)
                | Q(content__icontains=search_term)
            )

        return queryset.distinct()

    def perform_create(self, serializer):
        # Save the document and its first version atomically.
        with transaction.atomic():
            document = serializer.save()
            DocumentVersion.objects.create(
                document=document,
                content=document.content,
                version_number=document.versions.count() + 1,
                saved_by=document.created_by,
            )

    def perform_update(self, serializer):
        # Save the update and its version snapshot atomically.
        with transaction.atomic():
            document = serializer.save()
            DocumentVersion.objects.create(
                document=document,
                content=document.content,
                version_number=document.versions.count() + 1,
                saved_by=document.created_by,
            )

    @action(detail=True, methods=["get"], url_path="versions")
    def versions(self, request, pk=None):
        document = self.get_object()
        versions = document.versions.select_related("saved_by").order_by(
            "version_number"
        )
        serializer = DocumentVersionSerializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="stats")
    def stats(self, request, pk=None):
        document = self.get_object()

        counts = Document.objects.filter(pk=document.pk).aggregate(
            version_count=Count("versions", distinct=True),
            comment_count=Count("comments", distinct=True),
        )

        contributor_ids = set(
            document.versions.exclude(saved_by=None)
            .values_list("saved_by_id", flat=True)
            .distinct()
        )
        contributor_ids.update(
            document.comments.exclude(author=None)
            .values_list("author_id", flat=True)
            .distinct()
        )
        if document.created_by_id:
            contributor_ids.add(document.created_by_id)

        counts["unique_contributor_count"] = len(contributor_ids)
        return Response(counts)

    @action(detail=True, methods=["post"], url_path="tags")
    def tags(self, request, pk=None):
        document = self.get_object()
        tag_ids = request.data.get("tag_ids")

        if not isinstance(tag_ids, list) or not tag_ids:
            raise ValidationError(
                {"tag_ids": "Provide a non-empty list of tag UUIDs."}
            )

        tags = list(Tag.objects.filter(id__in=tag_ids))

        if len({str(tag.id) for tag in tags}) != len(
            {str(tag_id) for tag_id in tag_ids}
        ):
            raise ValidationError(
                {"tag_ids": "One or more tag IDs are invalid."}
            )

        document.tags.add(*tags)
        return Response(
            {"detail": "Tags associated successfully."},
            status=status.HTTP_200_OK,
        )


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer

    def get_queryset(self):
        queryset = Comment.objects.select_related(
            "document", "author", "parent"
        ).prefetch_related("replies__author")

        document_id = self.request.query_params.get("document")
        if document_id:
            queryset = queryset.filter(document_id=document_id)

        # Return top-level comments; their replies are nested by the serializer.
        return queryset.filter(parent__isnull=True)

    def perform_create(self, serializer):
        serializer.save()


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.prefetch_related("documents").all()
    serializer_class = TagSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        queryset = AuditLog.objects.select_related("actor").all()

        actor_id = self.request.query_params.get("actor")
        start_time = self.request.query_params.get("timestamp__gte")
        end_time = self.request.query_params.get("timestamp__lte")

        if actor_id:
            queryset = queryset.filter(actor_id=actor_id)

        if start_time:
            queryset = queryset.filter(timestamp__gte=start_time)

        if end_time:
            queryset = queryset.filter(timestamp__lte=end_time)

        return queryset


class DocumentVersionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DocumentVersion.objects.select_related(
        "document", "saved_by"
    ).all()
    serializer_class = DocumentVersionSerializer


class WorkspaceMemberViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WorkspaceMember.objects.select_related(
        "workspace", "user"
    ).all()
    serializer_class = WorkspaceMemberSerializer

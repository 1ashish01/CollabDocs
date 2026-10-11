
from rest_framework import serializers

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


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "password",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_phone(self, value):
        value = value.strip()
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("This phone number is already registered.")
        if not value.isdigit():
            raise serializers.ValidationError("Phone must contain digits only.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
    queryset=User.objects.all(),
    source="user",
    write_only=True,
)

    class Meta:
        model = WorkspaceMember
        fields = ["id", "workspace", "user", "user_id", "role", "joined_at"]
        read_only_fields = ["id", "workspace", "joined_at"]


class WorkspaceSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    owner_id = serializers.PrimaryKeyRelatedField(
    queryset=User.objects.all(),
    source="owner",
    write_only=True,
)
    members = WorkspaceMemberSerializer(many=True, read_only=True)
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Workspace
        fields = [
            "id",
            "name",
            "owner",
            "owner_id",
            "is_active",
            "created_at",
            "members",
            "member_count",
        ]
        read_only_fields = ["id", "created_at", "members", "member_count"]


class DocumentVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentVersion
        fields = [
            "id",
            "document",
            "content",
            "version_number",
            "saved_by",
            "saved_at",
        ]
        read_only_fields = ["id", "version_number", "saved_at"]


class DocumentSerializer(serializers.ModelSerializer):
    versions = DocumentVersionSerializer(many=True, read_only=True)
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "content",
            "workspace",
            "created_by",
            "status",
            "updated_at",
            "versions",
            "tags",
        ]
        read_only_fields = ["id", "created_by", "updated_at", "versions", "tags"]

    def get_tags(self, obj):
        return list(obj.tags.values("id", "name"))

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Document title cannot be empty.")
        return value.strip()


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="author",
        write_only=True,
        required=False,
        allow_null=True,
    )
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "document",
            "author",
            "author_id",
            "content",
            "parent",
            "created_at",
            "replies",
        ]
        read_only_fields = ["id", "author", "created_at", "replies"]

    def get_replies(self, obj):
        replies = obj.replies.select_related("author").all()
        return CommentSerializer(
            replies,
            many=True,
            context=self.context,
        ).data

    def validate(self, attrs):
        parent = attrs.get("parent")
        document = attrs.get("document")

        if parent and document and parent.document_id != document.id:
            raise serializers.ValidationError({
                "parent": "The parent comment must belong to the same document."
            })

        return attrs


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "documents"]
        read_only_fields = ["id"]


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor",
            "action",
            "model_name",
            "object_id",
            "timestamp",
        ]
        read_only_fields = ["id", "timestamp"]

class DocumentSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
    )
    versions = DocumentVersionSerializer(many=True, read_only=True)
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "content",
            "workspace",
            "created_by",
            "status",
            "updated_at",
            "versions",
            "tags",
        ]
        read_only_fields = ["id", "updated_at", "versions", "tags"]

    def get_tags(self, obj):
        return list(obj.tags.values("id", "name"))

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Document title cannot be empty."
            )
        return value.strip()

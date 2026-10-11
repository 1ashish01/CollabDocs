from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    AuditLog,
    Comment,
    Document,
    DocumentVersion,
    User,
    Workspace,
    WorkspaceMember,
)


class CollabDocsAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            phone="9876543210",
            password="TestPass@123",
        )

        self.workspace = Workspace.objects.create(
            name="Test Workspace",
            owner=self.user,
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.user,
            role=WorkspaceMember.Role.ADMIN,
        )

    def create_document(self, title="Test Document"):
        return Document.objects.create(
            title=title,
            content="Test document content.",
            workspace=self.workspace,
            created_by=self.user,
            status=Document.Status.DRAFT,
        )

    def test_user_creation_does_not_return_password(self):
        response = self.client.post(
            "/api/users/",
            {
                "first_name": "New",
                "last_name": "User",
                "email": "newuser@example.com",
                "phone": "9876543211",
                "password": "NewPass@123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)
        self.assertTrue(
            User.objects.filter(email="newuser@example.com").exists()
        )

    def test_workspace_creation_adds_owner_as_admin(self):
        response = self.client.post(
            "/api/workspaces/",
            {
                "name": "New Workspace",
                "owner_id": str(self.user.id),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        membership = WorkspaceMember.objects.get(
            workspace_id=response.data["id"],
            user=self.user,
        )
        self.assertEqual(membership.role, WorkspaceMember.Role.ADMIN)

    def test_duplicate_workspace_membership_returns_conflict(self):
        response = self.client.post(
            f"/api/workspaces/{self.workspace.id}/members/",
            {
                "user_id": str(self.user.id),
                "role": "admin",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        self.assertEqual(
            WorkspaceMember.objects.filter(
                workspace=self.workspace,
                user=self.user,
            ).count(),
            1,
        )

    def test_document_creation_creates_version_and_audit_log(self):
        response = self.client.post(
            "/api/documents/",
            {
                "title": "API Test Document",
                "content": "Initial document content.",
                "workspace": str(self.workspace.id),
                "created_by": str(self.user.id),
                "status": "draft",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        document_id = response.data["id"]

        version = DocumentVersion.objects.get(
            document_id=document_id,
            version_number=1,
        )
        self.assertEqual(version.content, "Initial document content.")
        self.assertEqual(version.saved_by, self.user)

        self.assertTrue(
            AuditLog.objects.filter(
                object_id=str(document_id),
                action="created",
                actor=self.user,
            ).exists()
        )

    def test_reply_cannot_belong_to_another_documents_comment(self):
        first_document = self.create_document("First Document")
        second_document = self.create_document("Second Document")

        parent_comment = Comment.objects.create(
            document=first_document,
            author=self.user,
            content="Parent comment.",
        )

        response = self.client.post(
            "/api/comments/",
            {
                "document": str(second_document.id),
                "author_id": str(self.user.id),
                "content": "Invalid reply.",
                "parent": str(parent_comment.id),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("parent", response.data)

        self.assertFalse(
            Comment.objects.filter(content="Invalid reply.").exists()
        )
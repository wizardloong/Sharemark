"""seed futures table

Revision ID: ad1bf397906e
Revises: a4ecbe997a27
Create Date: 2025-08-29 10:50:17.420447

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from repos.future_repo import saveFuture


# revision identifiers, used by Alembic.
revision: str = 'ad1bf397906e'
down_revision: Union[str, None] = 'a4ecbe997a27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    futures = [
        {
            "name": "Smart Tags",
            "slug": "smart-tags",
            "description": "Automatically categorize bookmarks with AI-powered tags for better organization.",
            "path": "images/future/smart_tags.png",
            "deadline_year": 2026,
            "deadline_quarter": 1,
        },
        {
            "name": "End-to-End Encryption",
            "slug": "end-to-end-encryption",
            "description": "Secure your sensitive bookmarks with hi-grade encryption that only you can access.",
            "path": "images/future/encryption.png",
            "deadline_year": 2026,
            "deadline_quarter": 1,
        },
        {
            "name": "Full-Text Search",
            "slug": "full-text-search",
            "description": "Search across the actual content of your bookmarked pages, not just titles and URLs.",
            "path": "images/future/search.png",
            "deadline_year": 2026,
            "deadline_quarter": 1,
        },
        {
            "name": "Continuous Sync",
            "slug": "continuous-sync",
            "description": "Real-time updates across all devices the moment a bookmark is added or changed.",
            "path": "images/future/sync.png",
            "deadline_year": 2026,
            "deadline_quarter": 1,
        },
        {
            "name": "Granular Permissions",
            "slug": "granular-permissions",
            "description": "Set different access levels (view, comment, edit) for each team member or contact.",
            "path": "images/future/permissions.png",
            "deadline_year": 2026,
            "deadline_quarter": 2,
        },
        {
            "name": "Version History",
            "slug": "version-history",
            "description": "Track changes and revert to previous versions of your bookmark folders when needed.",
            "path": "images/future/versioning.png",
            "deadline_year": 2026,
            "deadline_quarter": 2,
        },
        {
            "name": "Bookmark Health Check",
            "slug": "bookmark-health-check",
            "description": "Automatically detect duplicate bookmarks, dead links, and outdated documentation to keep your team’s knowledge base clean and reliable.",
            "path": "images/future/healthcheck.png",
            "deadline_year": 2026,
            "deadline_quarter": 2,
        },
        {
            "name": "Import/Export/Autobackup",
            "slug": "import-export-autobackup",
            "description": "Easily migrate bookmarks to and from other services with support for multiple formats.",
            "path": "images/future/export.png",
            "deadline_year": 2026,
            "deadline_quarter": 2,
        },
        {
            "name": "Mobile App",
            "slug": "mobile-app",
            "description": "Access and manage your bookmarks on the go with a dedicated mobile application.",
            "path": "images/future/mobile.png",
            "deadline_year": 2026,
            "deadline_quarter": 3,
        },
        {
            "name": "Offline Access",
            "slug": "offline-access",
            "description": "View and manage your bookmarks even without an internet connection.",
            "path": "images/future/offline.png",
            "deadline_year": 2026,
            "deadline_quarter": 3,
        },
    ]

    for future in futures:
        saveFuture(
            name=future["name"],
            slug=future["slug"],
            description=future["description"],
            icon_url="https://getsharemark.com/static/" + future["path"],
            icon_path=future["path"],
            deadline_yead=future["deadline_year"],
            deadline_quarter=future["deadline_quarter"],
        )

    pass


def downgrade() -> None:
    pass

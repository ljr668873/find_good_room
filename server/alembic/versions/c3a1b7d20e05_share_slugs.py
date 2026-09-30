"""share slugs: users.share_slug / listings.share_slug + landlord_slug，并回填存量行

Revision ID: c3a1b7d20e05
Revises: aa951c992660
Create Date: 2026-09-30

"""
import secrets

import sqlalchemy as sa
from alembic import op

revision = "c3a1b7d20e05"
down_revision = "aa951c992660"
branch_labels = None
depends_on = None


def slug() -> str:
    return secrets.token_urlsafe(6)[:8]


def upgrade() -> None:
    op.add_column("users", sa.Column("share_slug", sa.String(16), nullable=True))
    op.add_column("listings", sa.Column("share_slug", sa.String(16), nullable=True))
    op.add_column("listings", sa.Column("landlord_slug", sa.String(16), nullable=True))

    bind = op.get_bind()
    # 回填存量：用户随机 slug，房源随机 slug + 冗余其房东的 slug
    users = bind.execute(sa.text("SELECT id FROM users WHERE share_slug IS NULL")).fetchall()
    for (uid,) in users:
        bind.execute(
            sa.text("UPDATE users SET share_slug = :s WHERE id = :id"),
            {"s": slug(), "id": uid},
        )
    listings = bind.execute(sa.text("SELECT id, landlord_id FROM listings WHERE share_slug IS NULL")).fetchall()
    for lid, landlord_id in listings:
        bind.execute(
            sa.text("UPDATE listings SET share_slug = :s WHERE id = :id"),
            {"s": slug(), "id": lid},
        )
        bind.execute(
            sa.text(
                "UPDATE listings l JOIN users u ON u.id = l.landlord_id "
                "SET l.landlord_slug = u.share_slug WHERE l.id = :id"
            ),
            {"id": lid},
        )

    op.create_unique_constraint("uq_users_share_slug", "users", ["share_slug"])
    op.create_unique_constraint("uq_listings_share_slug", "listings", ["share_slug"])


def downgrade() -> None:
    op.drop_constraint("uq_listings_share_slug", "listings", type_="unique")
    op.drop_constraint("uq_users_share_slug", "users", type_="unique")
    op.drop_column("listings", "landlord_slug")
    op.drop_column("listings", "share_slug")
    op.drop_column("users", "share_slug")

"""initial schema

Revision ID: 4c09c13e267b
Revises: 
Create Date: 2026-11-14 20:54:58.116133

"""
from alembic import op

revision = '0001' # Убедитесь, что номер совпадает с тем, что в файле
down_revision = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    op.execute("""
        CREATE TABLE visitors (
            id            uuid        PRIMARY KEY,
            email         text        NOT NULL,
            display_name  text        NOT NULL,
            role          text        NOT NULL DEFAULT 'visitor',
            created_at    timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT visitors_email_unique      UNIQUE (email),
            CONSTRAINT visitors_email_not_blank   CHECK (length(trim(email)) > 0),
            CONSTRAINT visitors_name_not_blank    CHECK (length(trim(display_name)) > 0),
            CONSTRAINT visitors_role_allowed      CHECK (role IN ('visitor', 'admin'))
        )
    """)

    op.execute("""
        CREATE TABLE seats (
            id          uuid        PRIMARY KEY,
            code        text        NOT NULL,
            kind        text        NOT NULL,
            capacity    integer     NOT NULL,
            opens_at    time        NOT NULL,
            closes_at   time        NOT NULL,
            max_minutes integer     NOT NULL,
            is_active   boolean     NOT NULL DEFAULT true,
            created_at  timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT seats_code_unique        UNIQUE (code),
            CONSTRAINT seats_kind_allowed       CHECK (kind IN ('desk', 'meeting_room', 'phone_booth')),
            CONSTRAINT seats_capacity_positive  CHECK (capacity > 0),
            CONSTRAINT seats_hours_ordered      CHECK (opens_at < closes_at),
            CONSTRAINT seats_duration_positive  CHECK (max_minutes > 0)
        )
    """)

    op.execute("""
        CREATE TABLE bookings (
            id            uuid        PRIMARY KEY,
            seat_id       uuid        NOT NULL,
            user_id       uuid        NOT NULL,
            starts_at     timestamptz NOT NULL,
            ends_at       timestamptz NOT NULL,
            status        text        NOT NULL DEFAULT 'active',
            cancel_reason text,
            cancelled_by  uuid,
            created_at    timestamptz NOT NULL DEFAULT now(),
            cancelled_at  timestamptz,

            CONSTRAINT bookings_seat_fk
                FOREIGN KEY (seat_id) REFERENCES seats(id) ON DELETE RESTRICT,
            CONSTRAINT bookings_user_fk
                FOREIGN KEY (user_id) REFERENCES visitors(id) ON DELETE RESTRICT,
            CONSTRAINT bookings_cancelled_by_fk
                FOREIGN KEY (cancelled_by) REFERENCES visitors(id) ON DELETE SET NULL,

            CONSTRAINT bookings_period_positive CHECK (ends_at > starts_at),
            CONSTRAINT bookings_status_allowed
                CHECK (status IN ('active', 'cancelled', 'withdrawn', 'completed', 'no_show')),

            CONSTRAINT bookings_withdrawn_has_reason
                CHECK (status <> 'withdrawn' OR cancel_reason IS NOT NULL),

            CONSTRAINT bookings_cancelled_at_consistent
                CHECK ((status IN ('cancelled', 'withdrawn')) = (cancelled_at IS NOT NULL))
        )
    """)

    op.execute("""
        ALTER TABLE bookings ADD CONSTRAINT bookings_no_overlap
            EXCLUDE USING gist (
                seat_id WITH =,
                tstzrange(starts_at, ends_at, '[)') WITH &&
            ) WHERE (status = 'active')
    """)


def downgrade() -> None:
    op.execute("DROP TABLE bookings")
    op.execute("DROP TABLE seats")
    op.execute("DROP TABLE visitors")
    op.execute("DROP EXTENSION IF EXISTS btree_gist")

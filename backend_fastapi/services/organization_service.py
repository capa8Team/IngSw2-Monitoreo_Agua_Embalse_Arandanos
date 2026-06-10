"""Resolución de organizaciones por usuario (Supabase)."""

from __future__ import annotations



from dataclasses import dataclass

from typing import Optional



from sqlalchemy import text



from core.config import settings

from db.database import SessionLocal



DEFAULT_ORGANIZATION_SLUG = "embalse-arandanos"

DEFAULT_ORGANIZATION_NAME = "Embalse Arándanos"





@dataclass

class OrganizationInfo:

    id: str

    name: str

    slug: str

    org_role: str = "employee"





@dataclass

class UserOrganizationContext:

    organizations: list[OrganizationInfo]

    active_organization_id: Optional[str] = None



    @property

    def default_organization_id(self) -> Optional[str]:

        if self.organizations:

            return self.organizations[0].id

        return None





def _db_available() -> bool:

    return SessionLocal is not None





def fetch_user_organizations(user_id: str) -> list[OrganizationInfo]:

    if not _db_available() or not user_id:

        return []

    db = SessionLocal()

    try:

        rows = db.execute(

            text(

                """

                SELECT o.id::text, o.name, o.slug, uo.org_role

                FROM public.user_organizations uo

                JOIN public.organizations o ON o.id = uo.organization_id

                WHERE uo.user_id::text = :uid AND o.active = true

                ORDER BY o.name

                """

            ),

            {"uid": user_id},

        ).fetchall()

        return [

            OrganizationInfo(

                id=str(r[0]),

                name=str(r[1]),

                slug=str(r[2]),

                org_role=str(r[3] or "employee"),

            )

            for r in rows

        ]

    except Exception:

        db.rollback()

        return []

    finally:

        db.close()





def get_organization_by_id(organization_id: str) -> Optional[OrganizationInfo]:

    if not _db_available() or not organization_id:

        return None

    db = SessionLocal()

    try:

        row = db.execute(

            text(

                """

                SELECT id::text, name, slug

                FROM public.organizations

                WHERE id::text = :oid AND active = true

                LIMIT 1

                """

            ),

            {"oid": organization_id},

        ).fetchone()

        if not row:

            return None

        return OrganizationInfo(id=str(row[0]), name=str(row[1]), slug=str(row[2]))

    except Exception:

        db.rollback()

        return None

    finally:

        db.close()





def get_default_organization() -> Optional[OrganizationInfo]:

    slug = getattr(settings, "DEFAULT_ORGANIZATION_SLUG", None) or DEFAULT_ORGANIZATION_SLUG

    if not _db_available():

        return None

    db = SessionLocal()

    try:

        row = db.execute(

            text(

                """

                SELECT id::text, name, slug

                FROM public.organizations

                WHERE slug = :slug AND active = true

                LIMIT 1

                """

            ),

            {"slug": slug},

        ).fetchone()

        if not row:

            return None

        return OrganizationInfo(id=str(row[0]), name=str(row[1]), slug=str(row[2]))

    except Exception:

        db.rollback()

        return None

    finally:

        db.close()





def user_can_access_organization(*, user_id: str, organization_id: str) -> bool:

    return any(o.id == organization_id for o in fetch_user_organizations(user_id))





def resolve_user_organization_context(

    *,

    user_id: str,

    preferred_organization_id: Optional[str] = None,

) -> UserOrganizationContext:

    organizations = fetch_user_organizations(user_id)



    active_id: Optional[str] = None

    if preferred_organization_id and any(

        o.id == preferred_organization_id for o in organizations

    ):

        active_id = preferred_organization_id

    elif organizations:

        active_id = organizations[0].id

    else:

        default_org = get_default_organization()

        active_id = default_org.id if default_org else None



    return UserOrganizationContext(

        organizations=organizations,

        active_organization_id=active_id,

    )





def organizations_to_claims(organizations: list[OrganizationInfo]) -> list[dict]:

    return [

        {"id": o.id, "name": o.name, "slug": o.slug, "org_role": o.org_role}

        for o in organizations

    ]





def assign_user_to_organization(
    *,
    user_id: str,
    organization_id: str,
    org_role: str = "employee",
) -> tuple[bool, Optional[str]]:
    if not _db_available():
        return False, "Base de datos no disponible"

    normalized_role = "admin" if org_role in ("admin", "administrador") else "employee"
    db = SessionLocal()
    try:
        db.execute(
            text(
                """
                INSERT INTO public.user_organizations (user_id, organization_id, org_role)
                VALUES (CAST(:uid AS uuid), CAST(:oid AS uuid), :role)
                ON CONFLICT (user_id, organization_id) DO UPDATE
                SET org_role = EXCLUDED.org_role
                """
            ),
            {"uid": user_id, "oid": organization_id, "role": normalized_role},
        )
        db.commit()
        return True, None
    except Exception as exc:
        db.rollback()
        return False, str(exc)
    finally:
        db.close()


def user_is_org_admin(*, user_id: str, organization_id: str) -> bool:
    return any(
        o.id == organization_id and o.org_role == "admin"
        for o in fetch_user_organizations(user_id)
    )


def fetch_organization_member_emails(organization_id: str) -> set[str]:
    if not _db_available() or not organization_id:
        return set()
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                """
                SELECT lower(u.email)
                FROM auth.users u
                INNER JOIN public.user_organizations uo ON uo.user_id = u.id
                WHERE uo.organization_id = CAST(:oid AS uuid)
                """
            ),
            {"oid": organization_id},
        ).fetchall()
        return {str(r[0]) for r in rows if r and r[0]}
    except Exception:
        db.rollback()
        return set()
    finally:
        db.close()


def list_organization_auth_users(organization_id: str) -> list[dict]:
    if not _db_available() or not organization_id:
        return []
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                """
                SELECT
                  u.id::text,
                  u.email::text,
                  coalesce(
                    nullif(trim(ur.full_name), ''),
                    nullif(trim(u.raw_user_meta_data->>'full_name'), ''),
                    u.email::text
                  ) AS full_name,
                  coalesce(
                    nullif(trim(ur.role), ''),
                    nullif(trim(u.raw_user_meta_data->>'role'), ''),
                    'employee'
                  ) AS role,
                  u.created_at,
                  u.email_confirmed_at,
                  u.last_sign_in_at,
                  (u.email_confirmed_at IS NOT NULL OR u.last_sign_in_at IS NOT NULL) AS is_verified,
                  uo.org_role
                FROM auth.users u
                INNER JOIN public.user_organizations uo ON uo.user_id = u.id
                LEFT JOIN public.users_roles ur ON ur.id = u.id
                WHERE uo.organization_id = CAST(:oid AS uuid)
                ORDER BY u.created_at DESC NULLS LAST
                """
            ),
            {"oid": organization_id},
        ).fetchall()
        return [
            {
                "id": str(r[0]),
                "email": str(r[1] or ""),
                "full_name": str(r[2] or ""),
                "role": str(r[3] or "employee"),
                "created_at": r[4].isoformat() if r[4] else None,
                "email_confirmed_at": r[5].isoformat() if r[5] else None,
                "last_sign_in_at": r[6].isoformat() if r[6] else None,
                "is_verified": bool(r[7]),
                "org_role": str(r[8] or "employee"),
            }
            for r in rows
        ]
    except Exception:
        db.rollback()
        return []
    finally:
        db.close()


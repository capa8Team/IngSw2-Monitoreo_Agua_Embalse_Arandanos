"""Estado de primer acceso / contraseña pendiente (users_roles)."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import text

from db.database import SessionLocal


def _db_available() -> bool:
    return SessionLocal is not None


def _metadata_flag(value) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "t", "yes")


def _row_requires_setup(row) -> bool:
    if not row:
        return False
    db_flag = bool(row[0]) if row[0] is not None else False
    meta_flag = _metadata_flag(row[1]) if len(row) > 1 else False
    return db_flag or meta_flag


def get_must_set_password(*, user_id: str | None = None, email: str | None = None) -> bool:
    if not _db_available():
        return False
    if not user_id and not email:
        return False

    db = SessionLocal()
    try:
        if user_id:
            row = db.execute(
                text(
                    """
                    SELECT
                      COALESCE(ur.must_set_password, false),
                      u.raw_user_meta_data->>'must_set_password'
                    FROM auth.users u
                    LEFT JOIN public.users_roles ur ON ur.id = u.id
                    WHERE u.id::text = :uid
                    LIMIT 1
                    """
                ),
                {"uid": user_id},
            ).fetchone()
        else:
            row = db.execute(
                text(
                    """
                    SELECT
                      COALESCE(ur.must_set_password, false),
                      u.raw_user_meta_data->>'must_set_password'
                    FROM auth.users u
                    LEFT JOIN public.users_roles ur ON ur.id = u.id
                    WHERE lower(u.email) = lower(:email)
                    LIMIT 1
                    """
                ),
                {"email": email.strip()},
            ).fetchone()
        return _row_requires_setup(row)
    except Exception:
        db.rollback()
        try:
            if user_id:
                row = db.execute(
                    text(
                        """
                        SELECT u.raw_user_meta_data->>'must_set_password'
                        FROM auth.users u
                        WHERE u.id::text = :uid
                        LIMIT 1
                        """
                    ),
                    {"uid": user_id},
                ).fetchone()
            else:
                row = db.execute(
                    text(
                        """
                        SELECT u.raw_user_meta_data->>'must_set_password'
                        FROM auth.users u
                        WHERE lower(u.email) = lower(:email)
                        LIMIT 1
                        """
                    ),
                    {"email": email.strip()},
                ).fetchone()
            return _metadata_flag(row[0] if row else None)
        except Exception:
            db.rollback()
            return False
    finally:
        db.close()


def set_must_set_password(*, user_id: str, required: bool = True) -> tuple[bool, Optional[str]]:
    if not _db_available() or not user_id:
        return False, "Base de datos no disponible"

    db = SessionLocal()
    try:
        result = db.execute(
            text(
                """
                UPDATE public.users_roles
                SET must_set_password = :required, updated_at = NOW()
                WHERE id::text = :uid
                """
            ),
            {"uid": user_id, "required": required},
        )
        if result.rowcount == 0:
            db.rollback()
            return False, "Usuario no encontrado en users_roles"

        # Mantener auth.users metadata alineada (signUp guarda must_set_password ahí).
        if required:
            db.execute(
                text(
                    """
                    UPDATE auth.users
                    SET raw_user_meta_data = COALESCE(raw_user_meta_data, '{}'::jsonb)
                      || jsonb_build_object('must_set_password', true)
                    WHERE id::text = :uid
                    """
                ),
                {"uid": user_id},
            )
        else:
            db.execute(
                text(
                    """
                    UPDATE auth.users
                    SET raw_user_meta_data = COALESCE(raw_user_meta_data, '{}'::jsonb)
                      - 'must_set_password'
                    WHERE id::text = :uid
                    """
                ),
                {"uid": user_id},
            )

        db.commit()
        return True, None
    except Exception as exc:
        db.rollback()
        return False, str(exc)
    finally:
        db.close()


def email_requires_password_setup(email: str) -> bool:
    normalized = str(email or "").strip().lower()
    if not normalized:
        return False
    return get_must_set_password(email=normalized)

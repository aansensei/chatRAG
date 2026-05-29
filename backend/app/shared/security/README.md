## shared/security

Security utilities dùng chung.

Sẽ có: `create_access_token()` / `decode_token()` với JWT (python-jose), `hash_password()` / `verify_password()` với bcrypt. Không chứa business logic - chỉ là crypto helpers.

## presentation/middleware

FastAPI middleware that runs before each request.

### Files

`auth.py` - validates the JWT token from the Authorization header, decodes it, and populates `request.state.user`. Returns 401 if the token is invalid or expired.

`permission.py` - after auth, checks whether the user has the required right on the target resource (document-level). Calls the validate_access use case.

`rate_limit.py` - limits the number of requests per IP or per user within a time window to prevent abuse.

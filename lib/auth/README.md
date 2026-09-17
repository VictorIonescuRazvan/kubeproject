## Auth

`Auth` validates an API key and issues expiring UUID7 bearer tokens.

```python
from auth import Auth

auth = Auth(api_key="configured-key")
token = auth.get_token("configured-key")
assert token is not None
assert auth.auth(token)
```

When constructor values are omitted, `API_KEY` supplies the API key and
`TOKEN_EXPIRATION` supplies the token lifetime in seconds. `TOKEN_EXPIRY` is
also accepted as an alias. The default lifetime is five minutes.

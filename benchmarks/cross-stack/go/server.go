// Source snapshot: golang/go
// Upstream: https://github.com/golang/go/blob/409a267abaf0eb81e011f1ea90c0f8a78dd5d062/src/net/http/server.go
// ReadTimeout is the maximum duration for reading the entire
// request, including the body. A zero or negative value means
// there will be no timeout.
ReadTimeout time.Duration
// WriteTimeout is the maximum duration before timing out
// writes of the response.
WriteTimeout time.Duration

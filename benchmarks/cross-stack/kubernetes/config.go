// Source snapshot: kubernetes/kubernetes
// Upstream: https://github.com/kubernetes/kubernetes/blob/8df067da99ddbd208c3a2815c29471b8ab8a4677/staging/src/k8s.io/apiserver/pkg/server/config.go
// If specified, all requests except long-running requests will timeout.
RequestTimeout time.Duration
MaxRequestsInFlight int
MaxMutatingRequestsInFlight int
MaxRequestsInFlight:            400,
MaxMutatingRequestsInFlight:    200,
RequestTimeout:                 time.Duration(60) * time.Second,
MinRequestTimeout:              1800,

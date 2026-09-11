package main

import (
    caddycmd "github.com/caddyserver/caddy/v2/cmd"
    _ "github.com/caddyserver/caddy/v2/modules/standard"
    _ "github.com/corazawaf/coraza-caddy/v2"
)

func main() {
    caddycmd.Main()
}

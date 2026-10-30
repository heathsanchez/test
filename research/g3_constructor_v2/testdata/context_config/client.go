package client

import (
	"context"
	"errors"
	"time"
)

type Client struct { Ready bool }
type Settings struct { Capacity int }

func Defaults(d time.Duration) Settings { return Settings{Capacity:1} }
func Open(ctx context.Context, settings Settings) (*Client,error) {
	if ctx==nil || settings.Capacity<1 {return nil,errors.New("invalid config")}
	return &Client{Ready:true},nil
}

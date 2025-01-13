package main

import (
	"context"
	"koshechko/internal/database"
	"koshechko/internal/repository/lb"
	"koshechko/internal/repository/registry"
	"koshechko/internal/repository/session"
	temptoken "koshechko/internal/repository/temp_token"
	"koshechko/internal/service"
	"koshechko/internal/worker"
	"log"
	"time"

	red "github.com/redis/go-redis/v9"
)

func main() {
	ctx := context.Background()

	pg, err := database.MakePostgres(ctx, &database.Config{
		ConnString: "postgresql://root:DWCfSgJEmwhtUFNa4Grkx2@db:5432/koshechko",
		ConnCount:  10,
	})
	if err != nil {
		log.Fatalf("postgres: %s", err)
		return
	}

	qe := database.NewQE(pg)
	redis := red.NewClient(&red.Options{
		Addr: "redis:6379",
	})

	l := lb.NewLB(redis)
	reg := registry.NewRepoRegistry(qe)
	sess := session.NewRepo(redis)
	tok := temptoken.NewRepo(redis)

	app, err := service.Init(ctx, reg, sess, l, tok)
	if err != nil {
		log.Fatalf("init: %s", err)
		return
	}

	wrk := worker.New(worker.Config{
		ProcessName:      "Koshechko",
		ErrorDelay:       5 * time.Minute,
		OperationDelay:   300 * time.Millisecond,
		OperationTimeout: 5 * time.Second,
	}, &app)
	wrk.Start(ctx)

	app.Run()
}

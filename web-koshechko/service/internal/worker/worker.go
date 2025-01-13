package worker

import (
	"context"
	"koshechko/internal/repository/registry"
	"log/slog"
	"sync"
	"time"
)

type (
	Worker interface {
		ProcessName() string
		Start(context.Context)
		Stop()
		Close() error
	}

	Processor interface {
		Process(ctx context.Context) error
	}
)

func New(cfg Config, p Processor) *worker {
	return &worker{
		o:    sync.Once{},
		cfg:  cfg,
		p:    p,
		done: make(chan struct{}),
		wg:   sync.WaitGroup{},
	}
}

type worker struct {
	reg  registry.RepoRegistry
	cfg  Config
	p    Processor
	done chan struct{}
	wg   sync.WaitGroup

	o sync.Once
}

type Config struct {
	ProcessName      string
	ErrorDelay       time.Duration
	OperationDelay   time.Duration
	OperationTimeout time.Duration
}

func (w *worker) ProcessName() string {
	return w.cfg.ProcessName
}

func (w *worker) Start(ctx context.Context) {
	w.o.Do(func() {
		w.wg.Add(1)

		w.done = make(chan struct{})
		go w.run(ctx)
	})
}

func (w *worker) Stop() {
	w.Close()
	w.o = sync.Once{}
}

func (w *worker) run(ctx context.Context) {
	defer w.wg.Done()

	for {
		func() {
			ctxWithTimeout, cancel := context.WithTimeout(ctx, w.cfg.OperationTimeout)
			defer cancel()

			err := w.p.Process(ctxWithTimeout)
			if err != nil {
				slog.Error("err", "err", err)
				<-time.After(w.cfg.ErrorDelay)
				return
			}
		}()
		select {
		case <-w.done:
			return
		case <-time.After(w.cfg.OperationDelay):
		}
	}
}

func (w *worker) Close() error {
	close(w.done)
	w.wg.Wait()

	return nil
}

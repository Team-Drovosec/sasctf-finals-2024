package registry

import (
	"koshechko/internal/repository/koshechko"
	"koshechko/internal/repository/lb_queue"
	"koshechko/internal/repository/user"
)

func (r registry) User() user.Repository {
	if r.txHolder != nil {
		return user.New(r.txHolder)
	}

	return user.New(r.db)
}

func (r registry) Koshechko() koshechko.Repository {
	if r.txHolder != nil {
		return koshechko.New(r.txHolder)
	}

	return koshechko.New(r.db)
}

func (r registry) LBQueue() lb_queue.Repository {
	if r.txHolder != nil {
		return lb_queue.New(r.txHolder)
	}

	return lb_queue.New(r.db)
}

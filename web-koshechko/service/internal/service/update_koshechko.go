package service

import (
	"koshechko/internal/service/model"

	"github.com/gin-gonic/gin"
)

type updateKoshechkoReq struct {
	Name       string   `json:"name"`
	NewName    string   `json:"new_name"`
	Text       string   `json:"text"`
	SharedWith []string `json:"shared_with"`
}

type updateKoshechkoResp struct{}

func (s *Service) UpdateKoshechko(c *gin.Context) {
	ctx := c.Request.Context()

	username := c.GetString(UsernameKey)
	isValid := c.GetBool(IsValidKey)
	if !isValid {
		c.AbortWithStatus(403)
		return
	}

	req := updateKoshechkoReq{}
	if err := c.BindJSON(&req); err != nil {
		c.AbortWithStatus(513)
		return
	}

	k, err := s.reg.Koshechko().Get(ctx, req.Name)
	if err != nil {
		c.AbortWithStatus(412)
		return
	}

	if k.Owner != username {
		c.AbortWithStatus(413)
		return
	}

	err = s.reg.LBQueue().Push(ctx, model.QueueRecord{
		EventType:           model.ETUpdateKoshechko,
		KoshechkoName:       req.Name,
		KoshechkoNewName:    req.NewName,
		KoshechkoText:       req.Text,
		KoshechkoSharedWith: req.SharedWith,
	})
	if err != nil {
		c.AbortWithStatus(515)
		return
	}

	c.JSON(200, updateKoshechkoResp{})
}

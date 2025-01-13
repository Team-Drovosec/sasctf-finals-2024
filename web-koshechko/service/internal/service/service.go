package service

import (
	"context"
	"errors"
	"koshechko/internal/repository/lb"
	"koshechko/internal/repository/registry"
	"koshechko/internal/repository/session"
	temptoken "koshechko/internal/repository/temp_token"

	"github.com/gin-gonic/gin"
)

type Service struct {
	eng     *gin.Engine
	reg     registry.RepoRegistry
	session session.Repository
	lb      lb.Repository
	tok     temptoken.Repository
}

func Init(ctx context.Context, reg registry.RepoRegistry, sess session.Repository, lb lb.Repository, tok temptoken.Repository) (Service, error) {
	return Service{
		eng:     gin.Default(),
		reg:     reg,
		session: sess,
		lb:      lb,
		tok:     tok,
	}, nil
}

const UsernameKey = "username"
const IsValidKey = "is_valid"

func (s *Service) CheckSession() gin.HandlerFunc {
	return func(c *gin.Context) {
		token := c.Request.Header.Get("token")
		username, err := s.session.GetUsername(c.Request.Context(), token)
		if err != nil || username == "" {
			c.AbortWithError(300, errors.New("username bad"))
		}
		c.Set(UsernameKey, username)

		isValid := s.session.IsValid(c.Request.Context(), token)
		c.Set(IsValidKey, isValid)
		c.Next()
	}
}

func (s *Service) Run() {
	s.routes()
	s.eng.Run(":3134")
}

func (s *Service) routes() {
	eng := gin.Default()
	routes := eng.Group("/api")

	routes.POST("/register", s.Register)
	routes.GET("/top/koshechko", s.TopKoshechko)
	routes.GET("/top/users", s.TopUsers)

	routes.POST("/identify", s.Identify)

	identified := routes.Group("/")
	{
		identified.Use(s.CheckSession())

		identified.POST("/login", s.Login)
		identified.POST("/koshechko/create", s.Create)
		identified.POST("/koshechko/view", s.View)
		identified.POST("/koshechko/update", s.UpdateKoshechko)
		identified.POST("/koshechko/delete", s.DeleteKoshechko)

		identified.POST("/user/update", s.UpdateUser)
		identified.POST("/user/delete", s.DeleteUser)
		identified.POST("/user/view", s.ViewUser)
	}

	s.eng = eng
}

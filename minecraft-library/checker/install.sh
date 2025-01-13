#!/bin/bash

cd /checkers/mine/

export BUN_INSTALL="$HOME/.bun"
export PATH=$BUN_INSTALL/bin:$PATH

bun install
#!/bin/bash

cd /checkers/mine/

export BUN_INSTALL="$HOME/.bun"
export PATH=$BUN_INSTALL/bin:$PATH

# echo "bun run index.ts ${@:1}"
bun run index.ts ${@:1}


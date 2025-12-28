#!/bin/bash
# InvestMind Pro - 飞牛NAS Docker镜像构建脚本
# 用法: ./build-for-nas.sh [架构]
# 架构: amd64 (默认) 或 arm64

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 镜像名称
IMAGE_NAME="investmindpro"
IMAGE_TAG="latest"

# 获取架构参数
ARCH=${1:-amd64}

echo -e "${GREEN}=========================================="
echo "  InvestMind Pro - Docker镜像构建"
echo "  目标架构: ${ARCH}"
echo -e "==========================================${NC}"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker未安装，请先安装Docker${NC}"
    exit 1
fi

# 构建镜像
echo -e "${YELLOW}[1/3] 构建Docker镜像...${NC}"

if [ "$ARCH" = "arm64" ]; then
    # ARM64架构（适用于ARM版NAS）
    docker buildx build \
        --platform linux/arm64 \
        -f Dockerfile.all-in-one \
        -t ${IMAGE_NAME}:${IMAGE_TAG}-arm64 \
        --load \
        .
    FINAL_TAG="${IMAGE_TAG}-arm64"
else
    # AMD64架构（适用于x86 NAS）
    docker build \
        -f Dockerfile.all-in-one \
        -t ${IMAGE_NAME}:${IMAGE_TAG} \
        .
    FINAL_TAG="${IMAGE_TAG}"
fi

echo -e "${GREEN}镜像构建完成: ${IMAGE_NAME}:${FINAL_TAG}${NC}"

# 导出镜像
echo -e "${YELLOW}[2/3] 导出镜像为tar文件...${NC}"
OUTPUT_FILE="${IMAGE_NAME}-${FINAL_TAG}.tar"
docker save -o ${OUTPUT_FILE} ${IMAGE_NAME}:${FINAL_TAG}
echo -e "${GREEN}镜像已导出: ${OUTPUT_FILE}${NC}"

# 压缩镜像
echo -e "${YELLOW}[3/3] 压缩镜像文件...${NC}"
gzip -f ${OUTPUT_FILE}
COMPRESSED_FILE="${OUTPUT_FILE}.gz"
echo -e "${GREEN}压缩完成: ${COMPRESSED_FILE}${NC}"

# 显示文件大小
FILE_SIZE=$(ls -lh ${COMPRESSED_FILE} | awk '{print $5}')
echo ""
echo -e "${GREEN}=========================================="
echo "  构建完成!"
echo "  镜像文件: ${COMPRESSED_FILE}"
echo "  文件大小: ${FILE_SIZE}"
echo ""
echo "  部署步骤:"
echo "  1. 将 ${COMPRESSED_FILE} 上传到飞牛NAS"
echo "  2. 在NAS上执行: gunzip ${COMPRESSED_FILE}"
echo "  3. 导入镜像: docker load -i ${OUTPUT_FILE}"
echo "  4. 创建容器（参考 docker-compose-nas.yml）"
echo -e "==========================================${NC}"

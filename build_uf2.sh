#/bin/bash

echo "left/right = $1"

ZMK_ROOT="/zmk-firmware"
SHIELD_BASE="fish"
SHIELD="${SHIELD_BASE}_${1}"
APP_DIR="${ZMK_ROOT}/zmk/app"
BUILD_DIR="${ZMK_ROOT}/build/${SHIELD}"
CONFIG_DIR="${ZMK_ROOT}/config"
BOARD="seeeduino_xiao_ble"
KEYMAP="${CONFIG_DIR}/boards/shields/fish/fish.keymap"

touch ${KEYMAP}
west zephyr-export
west build -s ${APP_DIR} -b ${BOARD} -d ${BUILD_DIR} -- -DSHIELD=${SHIELD} -DZMK_CONFIG=${CONFIG_DIR}
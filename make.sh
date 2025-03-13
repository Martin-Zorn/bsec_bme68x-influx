#!/bin/sh

set  -e

. ./make.config

if [ ! -d "${BSEC_DIR}" ]; then
  echo 'BSEC directory missing.'
  exit 1
fi

STATEFILE="./bin/bsec_iaq.state"
if [ ! -f "${STATEFILE}" ]; then
  touch "${STATEFILE}"
fi

echo 'Patching...'
patch=patches/${DIFF_FILE}
if  patch -N --dry-run --silent ${BSEC_DIR}/examples/BSEC_Integration_Examples/examples/bsec_iot_example/bsec_integration.h \
    < "${patch}" >/dev/null
then
  echo 'Applying patch...'
  patch ${BSEC_DIR}/examples/BSEC_Integration_Examples/examples/bsec_iot_example/bsec_integration.h < ${patch}
else
  echo 'Already applied.'
fi

echo 'Compiling...'
gcc -Wall -Wno-unused-but-set-variable -Wno-unused-variable -static \
  -std=gnu99 \
  -pedantic \
  -fcommon \
  -g \
  -I${BSEC_DIR}/examples/BSEC_Integration_Examples/src/bme68x \
  -I${BSEC_DIR}/examples/BSEC_Integration_Examples/src/inc \
  -I${BSEC_DIR}/examples/BSEC_Integration_Examples/examples/bsec_iot_example \
  -I./src/bsec2-6-1-0_generic_release_22102024/algo/${BSEC_SOLUTION}/inc \
    ${BSEC_DIR}/examples/BSEC_Integration_Examples/src/bme68x/bme68x.c \
    ${BSEC_DIR}/examples/BSEC_Integration_Examples/src/bme68x/bme68x_defs.h \
    ${BSEC_DIR}/examples/BSEC_Integration_Examples/examples/bsec_iot_example/bsec_integration.c \
    ./src/bsec_bme68x.c \
  -L"${BSEC_DIR}/algo/${BSEC_SOLUTION}/bin/${BSEC_PLATFORM}/${BSEC_ARCH}" -lalgobsec \
  -lm -lrt \
  -o ./bin/bsec_bme68x
echo 'Compiled.'

cp ${BSEC_DIR}/algo/${BSEC_SOLUTION}/config/${BSEC_SENSOR}/${BSEC_SENSOR_CONFIG}/bsec_iaq.config ./bin
echo 'Copied config.'

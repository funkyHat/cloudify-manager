#/bin/bash -e

export AWS_S3_PATH="org/cloudify3/components"

CORE_TAG_NAME="3.4m5"
curl https://raw.githubusercontent.com/cloudify-cosmo/cloudify-packager/${PACKAGER_BRANCH-$CORE_TAG_NAME}/common/provision.sh -o ./common-provision.sh &&
source common-provision.sh

AWS_ACCESS_KEY_ID=$1
AWS_ACCESS_KEY=$2
MANAGER_BRANCH=$3
PACKAGER_BRANCH=$4

install_common_prereqs &&

rm -rf cloudify-manager
git clone https://github.com/cloudify-cosmo/cloudify-manager.git
cd cloudify-manager
git checkout ${MANAGER_BRANCH-$CORE_TAG_NAME}
cd packaging/elasticsearch_curator/omnibus
git tag -d $CORE_TAG_NAME
NEW_TAG_NAME="${VERSION}.${PRERELEASE}"
git tag $NEW_TAG_NAME
omnibus build elasticsearch-curator && result="success"
cd pkg
cat *.json || exit 1
rm -f version-manifest.json

[ "$result" == "success" ] && create_md5 "rpm" &&
[ -z ${AWS_ACCESS_KEY} ] || upload_to_s3 "rpm" && upload_to_s3 "md5" && upload_to_s3 "json"

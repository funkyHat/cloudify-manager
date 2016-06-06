name "plugins-common"

ENV['CORE_TAG_NAME'] || raise('CORE_TAG_NAME environment variable not set')
default_version ENV['CORE_TAG_NAME']

source :git => "https://github.com/cloudify-cosmo/cloudify-plugins-common"

build do
  command ["#{install_dir}/embedded/bin/pip",
           "install", "--build=#{project_dir}/#{name}", "."]
end
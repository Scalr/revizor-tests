# -*- mode: ruby -*-
# vi: set ft=ruby :

require 'yaml'

options = File.exist?('vagrant.yml')? YAML.load_file('vagrant.yml'): Hash.new

boxes = {
    "ubuntu" => {
        "box" => "ubuntu/xenial64",
        "url" => "https://app.vagrantup.com/ubuntu/boxes/xenial64"
    }
}

Vagrant.configure("2") do |config|
    config.vm.network "forwarded_port", guest: 4444, host: 4444, auto_correct: true

    if Vagrant.has_plugin?("vagrant-cachier")
        config.cache.scope = :box
    end

    config.vm.provider "virtualbox" do |v|
        v.memory = options["memory"] ||= 4096 
        v.cpus = options["cpus"] ||= 1
    end

    config.vm.box = "ubuntu/xenial64"
    config.vm.box_url = "https://app.vagrantup.com/ubuntu/boxes/xenial64"

    config.vm.provider :virtualbox do |vbox|
        vbox.customize ["setextradata", :id, "VBoxInternal/Devices/VMMDev/0/Config/GetHostTimeDisabled", options["get_host_time_disabled"] ||= "0"]
    end

    config.vm.synced_folder ".", "/vagrant"
    config.vm.synced_folder "../revizor", "/vagrant/revizor"

    config.vm.provision "base", type: "shell" do |shell|
        shell.path = "ui/ci/ubuntu.sh"
    end

    config.vm.provision "rsync-shared-folders", type: "shell" do |shell|
        shell.inline = "echo 'done.'"
    end
end
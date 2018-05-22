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

    boxes.each do |name, box|
        config.vm.define name do |machine|
            machine.vm.box = box["box"]
            machine.vm.box_url = box["url"]

            machine.vm.provider :virtualbox do |vbox|
                vbox.customize ["setextradata", :id, "VBoxInternal/Devices/VMMDev/0/Config/GetHostTimeDisabled", options["get_host_time_disabled"] ||= "0"]
            end

            machine.vm.synced_folder ".", "/vagrant", type: "rsync",
                rsync__excludes: [".git/"]

            machine.vm.provision "base", type: "shell" do |shell|
                shell.path = "ubuntu.sh"
            end

            machine.vm.provision "rsync-shared-folders", type: "shell" do |shell|
                shell.inline = "echo 'done.'"
            end
        end
    end
end
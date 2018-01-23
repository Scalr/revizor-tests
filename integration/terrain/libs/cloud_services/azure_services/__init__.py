import event_hubs
import container_registry
import machine_learning
import web


services = {
    event_hubs.EventHubs.service_name: event_hubs.EventHubs,
    web.Web.service_name: web.Web,
    machine_learning.MachineLearning.service_name: machine_learning.MachineLearning,
    container_registry.ContainerRegistry.service_name: container_registry.ContainerRegistry
}

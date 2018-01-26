import event_hubs
import container_registry
import container_service
import database
import machine_learning
import web


services = {
    event_hubs.EventHubs.service_name: event_hubs.EventHubs,
    web.Web.service_name: web.Web,
    machine_learning.MachineLearning.service_name: machine_learning.MachineLearning,
    container_registry.ContainerRegistry.service_name: container_registry.ContainerRegistry,
    container_service.ContainerService.service_name: container_service.ContainerService,
    database.Database.service_name: database.Database
}

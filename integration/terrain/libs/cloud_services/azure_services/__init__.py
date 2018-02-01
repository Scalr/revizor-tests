import container_registry
import container_service
import database
import event_hubs
import insights
import machine_learning
import stream_analytics
import web


services = {
    container_registry.ContainerRegistry.service_name: container_registry.ContainerRegistry,
    container_service.ContainerService.service_name: container_service.ContainerService,
    database.Database.service_name: database.Database,
    event_hubs.EventHubs.service_name: event_hubs.EventHubs,
    insights.Insights.service_name: insights.Insights,
    machine_learning.MachineLearning.service_name: machine_learning.MachineLearning,
    stream_analytics.StreamAnalytics.service_name: stream_analytics.StreamAnalytics,
    web.Web.service_name: web.Web
}

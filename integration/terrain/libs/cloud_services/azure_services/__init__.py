import event_hubs
import web


services = {
    event_hubs.EventHubs.service_name: event_hubs.EventHubs,
    web.Web.service_name: web.Web
}
import unittest
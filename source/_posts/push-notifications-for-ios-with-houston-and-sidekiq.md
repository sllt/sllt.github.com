title: 使用Houston+Sidekiq做ios消息推送
date: 2015-01-08 16:05:35
tags: rails
---
创建`NotifierWorker`类
```ruby
# app/workers/notifier_worker.rb
require 'apn_connection'
class NotifierWorker
  include Sidekiq::Worker

  APN_POOL = ConnectionPool.new(:size => 2, :timeout => 300) do
    APNConnection.new
  end
​
  def perform(message,  custom_data = nil)
    APN_POOL.with do |connection|
      token = "<dccec3dd 25936d87 5ed2d16b 75f0785c bdb0b33d 8dd48f1c 72529c00 b1c56a19>"
      notification = Houston::Notification.new(device: token)
      notification.alert = message
      notification.sound = 'default'
      notification.custom_data = custom_data
      connection.write(notification.message)
    end
  end
end
```
创建`APNConnection`类
```ruby
# lib/apn_connection.rb
class APNConnection

  def initialize
    setup
  end

  def setup
    @uri, @certificate = if Rails.env.production?
      [
        Houston::APPLE_PRODUCTION_GATEWAY_URI,
        File.read("#{Rails.root}/config/shixian-production.pem")
      ]
    else
      [
        Houston::APPLE_DEVELOPMENT_GATEWAY_URI,
        File.read("#{Rails.root}/config/shixian-development.pem")
      ]
    end

    @connection = Houston::Connection.new(@uri, @certificate, nil)
    @connection.open
  end

  def write(data)
    begin
      raise "Connection is closed" unless @connection.open?
      @connection.write(data)
    rescue Exception => e
      attempts ||= 0
      attempts += 1

      if attempts < 5
        setup
        retry
      else
        raise e
      end
    end
  end

end
```
使用
```
NotifierWorker.perform_async("hello","s" => "1,Notification")
```
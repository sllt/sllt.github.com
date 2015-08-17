title: 使用faye + sidekiq制作实时消息队列
date: 2015-08-17 14:35:52
tags: rails
---

## 使用faye + sidekiq制作实时消息队列

install faye and sidekiq

```ruby
# Gemfile


# Faye
gem 'faye-rails', '~> 2.0.0'
gem 'faye-redis', '~> 0.2.0'
gem 'faye',       '1.0.3'

# sidekiq
gem 'sidekiq'

```

编辑 config/application.rb

```ruby
config.middleware.use FayeRails::Middleware, mount: '/faye', engine: {type: Faye::Redis, uri: "#{ENV['REDIS_URL']}/4"}, :timeout => 25 do
     map '/api/questions/status' => Api::QuestionStateController
end
```

增加worker类

```ruby
# app/workers/question_state_worker.rb
class QuestionStateWorker
  include Sidekiq::Worker


  def get_question_state(user_id)
    Question.where("user_id = ? and finished= ?", user_id, false).select("id,user_id,has_teacher_answer").to_json
  end

  def keep_state(user_id, data)
    $redis.set "questions_state_#{user_id}", data
  end

  def perform(user_id)
    keep_state(user_id, get_question_state(user_id))
  end

end
```

监听数据库

```ruby

# app/realtime/api/question_state_controller.rb
class Api::QuestionStateController < FayeRails::Controller
  observe Question, :after_save do |question|
    QuestionStateWorker.perform_async(question.user_id)
  end

end
```
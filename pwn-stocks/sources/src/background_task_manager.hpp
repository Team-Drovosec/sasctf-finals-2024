#pragma once

#include <mutex>
#include <userver/components/component.hpp>
#include <userver/components/component_base.hpp>
#include <userver/concurrent/background_task_storage.hpp>
#include <userver/engine/task/task_with_result.hpp>

namespace tt {
    class BackgroundTaskManager : public userver::components::ComponentBase
    {
    public:
        static constexpr std::string_view kName = "background-task-manager";

        BackgroundTaskManager(const userver::components::ComponentConfig& config,
                              const userver::components::ComponentContext& context)
            : LoggableComponentBase(config, context)
        {}

        template<typename... Args>
        void AddTask(const std::string& name, Args&&... args)
        {
            std::lock_guard<std::mutex> lock(mutex_);
            bts_.AsyncDetach(name, std::forward<Args>(args)...);
        }

        ~BackgroundTaskManager() override
        {
            std::lock_guard<std::mutex> lock(mutex_);
            bts_.CancelAndWait();
        }

    private:
        userver::concurrent::BackgroundTaskStorage bts_;
        std::mutex mutex_; // Protects access to bts_
    };
};

#pragma once

#include <fstream>
#include <string>
#include <vector>

namespace voi_bw {

struct CommandEnvelope {
    std::string json;
};

class CommanderBridge {
public:
    explicit CommanderBridge(std::string queuePath) : queuePath_(std::move(queuePath)) {}

    std::vector<CommandEnvelope> poll() {
        std::ifstream input(queuePath_);
        std::vector<CommandEnvelope> commands;
        std::string line;
        while (std::getline(input, line)) {
            if (!line.empty()) {
                commands.push_back(CommandEnvelope{line});
            }
        }
        return commands;
    }

private:
    std::string queuePath_;
};

}  // namespace voi_bw

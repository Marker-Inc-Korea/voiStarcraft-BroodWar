#pragma once

#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace voi_bw {

struct CommandEnvelope {
    std::string json;
    unsigned long long sequence = 0;
    unsigned long long byteOffset = 0;
    bool valid = true;
    std::string error;
};

class CommanderBridge {
public:
    explicit CommanderBridge(std::string queuePath) : queuePath_(std::move(queuePath)) {}

    std::vector<CommandEnvelope> poll() {
        return pollNew();
    }

    std::vector<CommandEnvelope> pollNew() {
        std::ifstream input(queuePath_);
        std::vector<CommandEnvelope> commands;
        if (!input.good()) {
            return commands;
        }
        input.seekg(static_cast<std::streamoff>(byteOffset_));
        std::string line;
        while (std::getline(input, line)) {
            const auto lineStart = byteOffset_;
            byteOffset_ = static_cast<unsigned long long>(input.tellg() < 0 ? byteOffset_ + line.size() + 1 : input.tellg());
            if (!line.empty()) {
                commands.push_back(validateLine(line, lineStart));
            }
        }
        return commands;
    }

    void resetCursor() {
        byteOffset_ = 0;
        sequence_ = 0;
    }

    unsigned long long byteOffset() const {
        return byteOffset_;
    }

private:
    CommandEnvelope validateLine(const std::string& line, unsigned long long lineStart) {
        CommandEnvelope envelope;
        envelope.json = line;
        envelope.sequence = ++sequence_;
        envelope.byteOffset = lineStart;
        const auto first = line.find_first_not_of(" \t\r\n");
        if (first == std::string::npos || (line[first] != '{' && line[first] != '[')) {
            envelope.valid = false;
            envelope.error = "queue line is not a JSON object or array";
        }
        return envelope;
    }

    std::string queuePath_;
    unsigned long long byteOffset_ = 0;
    unsigned long long sequence_ = 0;
};

}  // namespace voi_bw

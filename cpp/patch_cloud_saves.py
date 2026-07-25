#!/usr/bin/env python3
"""Generate the C++ source with cloud save support patched in."""

from __future__ import annotations

import sys
from pathlib import Path


HELPERS = r'''

constexpr const char* DEFAULT_CLOUD_API_URL = "https://lordfunion.dev/adventure-api";
constexpr const char* CLOUD_SESSION_PATH = "saves/cpp_cloud_session.txt";

struct CloudSession {
    std::string username;
    std::string token;

    bool signed_in() const {
        return !username.empty() && !token.empty();
    }
};

std::string json_escape(const std::string& value) {
    std::ostringstream out;
    for (char ch : value) {
        switch (ch) {
            case '\\': out << "\\\\"; break;
            case '"': out << "\\\""; break;
            case '\n': out << "\\n"; break;
            case '\r': out << "\\r"; break;
            case '\t': out << "\\t"; break;
            default:
                if (static_cast<unsigned char>(ch) < 0x20) {
                    out << "\\u" << std::hex << std::uppercase << static_cast<int>(static_cast<unsigned char>(ch));
                } else {
                    out << ch;
                }
        }
    }
    return out.str();
}

std::string json_unescape(const std::string& value) {
    std::string out;
    for (std::size_t i = 0; i < value.size(); ++i) {
        if (value[i] != '\\' || i + 1 >= value.size()) {
            out.push_back(value[i]);
            continue;
        }
        char next = value[++i];
        if (next == 'n') out.push_back('\n');
        else if (next == 'r') out.push_back('\r');
        else if (next == 't') out.push_back('\t');
        else if (next == '"') out.push_back('"');
        else if (next == '\\') out.push_back('\\');
        else out.push_back(next);
    }
    return out;
}

std::string json_string_value(const std::string& json, const std::string& key) {
    std::regex pattern("\\\"" + key + "\\\"\\s*:\\s*\\\"((?:\\\\.|[^\\\"\\\\])*)\\\"");
    std::smatch match;
    if (!std::regex_search(json, match, pattern)) {
        return "";
    }
    return json_unescape(match[1].str());
}

bool json_ok(const std::string& json) {
    static const std::regex ok_pattern("\\\"ok\\\"\\s*:\\s*true");
    return std::regex_search(json, ok_pattern);
}

std::string shell_quote(const std::string& value) {
#ifdef _WIN32
    std::string escaped = "\"";
    for (char ch : value) {
        if (ch == '"') {
            escaped += "\\\"";
        } else {
            escaped.push_back(ch);
        }
    }
    escaped += "\"";
    return escaped;
#else
    std::string escaped = "'";
    for (char ch : value) {
        if (ch == '\'') {
            escaped += "'\\''";
        } else {
            escaped.push_back(ch);
        }
    }
    escaped += "'";
    return escaped;
#endif
}

std::string run_command_capture(const std::string& command) {
#ifdef _WIN32
    FILE* pipe = _popen(command.c_str(), "r");
#else
    FILE* pipe = popen(command.c_str(), "r");
#endif
    if (!pipe) {
        throw std::runtime_error("Could not start curl. Install curl or check your PATH.");
    }

    std::array<char, 4096> buffer{};
    std::string output;
    while (std::fgets(buffer.data(), static_cast<int>(buffer.size()), pipe)) {
        output += buffer.data();
    }

#ifdef _WIN32
    int status = _pclose(pipe);
#else
    int status = pclose(pipe);
#endif
    if (status != 0 && output.empty()) {
        throw std::runtime_error("curl failed before the cloud server returned a response.");
    }
    return output;
}

std::string cloud_endpoint(const std::string& action) {
    return std::string(DEFAULT_CLOUD_API_URL) + "/index.php?action=" + action;
}

std::string cloud_request(const std::string& action, const std::string& fields, const std::string& token = "") {
    fs::create_directories("saves");
    const auto stamp = std::chrono::steady_clock::now().time_since_epoch().count();
    fs::path payload_path = fs::path("saves") / ("cpp_cloud_request_" + std::to_string(stamp) + ".json");

    std::ostringstream payload;
    payload << "{\"action\":\"" << json_escape(action) << "\"";
    if (!token.empty()) {
        payload << ",\"token\":\"" << json_escape(token) << "\"";
    }
    if (!fields.empty()) {
        payload << "," << fields;
    }
    payload << "}";

    {
        std::ofstream out(payload_path);
        if (!out) {
            throw std::runtime_error("Could not write temporary cloud request.");
        }
        out << payload.str();
    }

    std::string command = "curl -sS -X POST -H " + shell_quote("Content-Type: application/json") +
        " -H " + shell_quote("Accept: application/json") +
        " --data-binary @" + shell_quote(payload_path.string()) + " " + shell_quote(cloud_endpoint(action));
    std::string response = run_command_capture(command);
    std::error_code ignored;
    fs::remove(payload_path, ignored);

    if (!json_ok(response)) {
        std::string error = json_string_value(response, "error");
        if (error.empty()) {
            error = json_string_value(response, "message");
        }
        if (error.empty()) {
            error = "Cloud save server returned an unreadable error.";
        }
        throw std::runtime_error(error);
    }
    return response;
}

CloudSession read_cloud_session() {
    CloudSession session;
    std::ifstream in(CLOUD_SESSION_PATH);
    if (!in) {
        return session;
    }
    std::getline(in, session.username);
    std::getline(in, session.token);
    session.username = trim(session.username);
    session.token = trim(session.token);
    return session;
}

void write_cloud_session(const CloudSession& session) {
    fs::create_directories(fs::path(CLOUD_SESSION_PATH).parent_path());
    std::ofstream out(CLOUD_SESSION_PATH);
    if (!out) {
        throw std::runtime_error("Could not save cloud session.");
    }
    out << session.username << "\n" << session.token << "\n";
}

void sign_out_cloud() {
    std::error_code ignored;
    fs::remove(CLOUD_SESSION_PATH, ignored);
}

std::string cloud_status() {
    CloudSession session = read_cloud_session();
    if (session.signed_in()) {
        return "Cloud: signed in as " + session.username;
    }
    return "Cloud: not signed in";
}

std::string make_save_text(const State& state) {
    std::ostringstream out;
    const Player& p = state.player;
    out << "AdventureGameCppSaveV3\n";
    out << state.next_scene << "\n";
    out << p.name << "\n";
    out << p.money << "\n" << p.health << "\n" << p.health_max << "\n" << p.mana << "\n"
        << p.mana_max << "\n" << p.armor << "\n" << p.weapon_damage << "\n" << p.extra_damage << "\n";
    out << (p.frog_mode ? 1 : 0) << "\n" << p.frog_power << "\n" << p.frog_energy << "\n" << p.frog_energy_max << "\n";

    auto write_values = [&out](const std::vector<std::string>& values) {
        out << values.size() << "\n";
        for (const std::string& value : values) {
            out << value << "\n";
        }
    };

    write_values(p.backpack);
    write_values(p.spells);
    write_values(p.frog_attacks);
    out << state.shop_stock.size() << "\n";
    for (const auto& [item, stocked] : state.shop_stock) {
        out << item << "\n" << (stocked ? 1 : 0) << "\n";
    }
    return out.str();
}

std::string safe_slot_name(const std::string& value) {
    std::string safe;
    for (char ch : value) {
        if (std::isalnum(static_cast<unsigned char>(ch)) || ch == '_' || ch == '-' || ch == '.') {
            safe.push_back(ch);
        }
    }
    return safe.empty() ? "autosave" : safe.substr(0, 64);
}

void cloud_register() {
    std::string username = ask("\nChoose cloud username: ");
    if (username.empty()) {
        say("\nNo username entered.");
        return;
    }
    std::string password = ask("Choose cloud password: ");
    std::string confirm = ask("Confirm cloud password: ");
    if (password != confirm) {
        say("\nPasswords did not match.");
        return;
    }

    std::string response = cloud_request(
        "register",
        "\"username\":\"" + json_escape(username) + "\",\"password\":\"" + json_escape(password) + "\""
    );
    CloudSession session;
    session.username = json_string_value(response, "username");
    session.token = json_string_value(response, "token");
    if (!session.signed_in()) {
        throw std::runtime_error("Cloud server did not return a login token.");
    }
    write_cloud_session(session);
    say("\nSigned in to cloud saves as " + session.username + ".");
}

void cloud_login() {
    std::string username = ask("\nCloud username: ");
    if (username.empty()) {
        say("\nNo username entered.");
        return;
    }
    std::string password = ask("Cloud password: ");

    std::string response = cloud_request(
        "login",
        "\"username\":\"" + json_escape(username) + "\",\"password\":\"" + json_escape(password) + "\""
    );
    CloudSession session;
    session.username = json_string_value(response, "username");
    session.token = json_string_value(response, "token");
    if (!session.signed_in()) {
        throw std::runtime_error("Cloud server did not return a login token.");
    }
    write_cloud_session(session);
    say("\nSigned in to cloud saves as " + session.username + ".");
}

bool cloud_upload_state(const State& state, const std::string& default_slot = "autosave", bool quiet = false) {
    CloudSession session = read_cloud_session();
    if (!session.signed_in()) {
        if (!quiet) {
            say("\nSign in before uploading cloud saves.");
        }
        return false;
    }
    std::string slot = default_slot;
    if (!quiet) {
        std::string typed = ask("\nCloud save slot [" + default_slot + "]: ");
        if (!typed.empty()) {
            slot = typed;
        }
    }
    slot = safe_slot_name(slot);
    cloud_request(
        "upload",
        "\"slot_name\":\"" + json_escape(slot) + "\",\"save_data\":\"" + json_escape(make_save_text(state)) + "\"",
        session.token
    );
    if (!quiet) {
        say("\nUploaded cloud save slot '" + slot + "'.");
    }
    return true;
}

bool cloud_download_interactive(State& loaded_state) {
    CloudSession session = read_cloud_session();
    if (!session.signed_in()) {
        say("\nSign in before loading cloud saves.");
        return false;
    }
    std::string slot = safe_slot_name(ask("\nCloud save slot to download [autosave]: "));
    std::string response = cloud_request(
        "download",
        "\"slot_name\":\"" + json_escape(slot) + "\"",
        session.token
    );
    std::string save_data = json_string_value(response, "save_data");
    if (save_data.empty()) {
        throw std::runtime_error("Cloud save server did not return save data.");
    }

    fs::create_directories("saves");
    std::string local_path = "saves/cpp_cloud_" + slot + ".cppsave";
    {
        std::ofstream out(local_path);
        if (!out) {
            throw std::runtime_error("Could not write downloaded cloud save.");
        }
        out << save_data;
    }
    loaded_state = load_state(local_path);
    save_state(loaded_state);
    say("\nDownloaded cloud save slot '" + slot + "' to " + local_path + ".");
    say("Loaded cloud save.");
    return true;
}

bool cloud_menu(State* current_state, State& loaded_state) {
    while (true) {
        CloudSession session = read_cloud_session();
        std::vector<MenuOption> options;
        if (session.signed_in()) {
            int next_key = 1;
            if (current_state != nullptr) {
                options.push_back({std::to_string(next_key++), "Upload Current Save", "upload", "", {"upload", "sync", "save"}});
            }
            options.push_back({std::to_string(next_key++), "Download Cloud Save", "download", "type a slot name", {"download", "load"}});
            options.push_back({std::to_string(next_key++), "Sign Out", "logout", "", {"logout", "sign out"}});
            options.push_back({std::to_string(next_key++), "Back", "back", "", {"back", "cancel"}});
        } else {
            options = {
                {"1", "Create Account", "register", "", {"register", "create"}},
                {"2", "Sign In", "login", "", {"login", "sign in"}},
                {"3", "Back", "back", "", {"back", "cancel"}},
            };
        }

        std::string choice = choose_menu("Cloud Saves", options, "Cloud choice: ", cloud_status());
        try {
            if (choice == "register") {
                cloud_register();
            } else if (choice == "login") {
                cloud_login();
            } else if (choice == "upload") {
                cloud_upload_state(*current_state);
            } else if (choice == "download") {
                if (cloud_download_interactive(loaded_state)) {
                    return true;
                }
            } else if (choice == "logout") {
                sign_out_cloud();
                say("\nSigned out of cloud saves on this device.");
            } else if (choice == "back") {
                return false;
            }
        } catch (const std::exception& exc) {
            say(std::string("\nCloud save failed: ") + exc.what());
        }
    }
}

bool cloud_autosync(const State& state) {
    try {
        return cloud_upload_state(state, "autosave", true);
    } catch (const std::exception&) {
        return false;
    }
}
'''


def require_replace(text: str, old: str, new: str) -> str:
    if old not in text:
        raise SystemExit(f"patch marker not found:\n{old}")
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: patch_cloud_saves.py <input.cpp> <output.cpp>")

    source_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    text = source_path.read_text(encoding="utf-8")

    text = require_replace(text, "#include <algorithm>\n", "#include <algorithm>\n#include <array>\n#include <chrono>\n")
    text = require_replace(text, "#include <sstream>\n", "#include <sstream>\n#include <regex>\n")
    text = require_replace(
        text,
        "bool checkpoint_menu(State& state) {\n",
        HELPERS + "\nbool checkpoint_menu(State& state) {\n",
    )
    text = require_replace(
        text,
        '        std::string subtitle = "Next: " + scene_title(state.next_scene) + " | Autosave: " + SAVE_PATH;\n',
        '        std::string subtitle = "Next: " + scene_title(state.next_scene) + " | Autosave: " + SAVE_PATH + " | " + cloud_status();\n',
    )
    text = require_replace(
        text,
        '        } else if (choice == "cloud") {\n            say("\\nCloud saves are not available in the C++ port.");\n',
        '        } else if (choice == "cloud") {\n            State loaded_state;\n            if (cloud_menu(&state, loaded_state)) {\n                state = loaded_state;\n                return true;\n            }\n',
    )
    text = require_replace(
        text,
        '        if (autosave_state(state)) {\n            say("\\nCheckpoint autosaved locally.");\n        }\n',
        '        if (autosave_state(state)) {\n            std::string message = "\\nCheckpoint autosaved locally.";\n            if (cloud_autosync(state)) {\n                message += " Cloud synced.";\n            }\n            say(message);\n        }\n',
    )
    text = require_replace(
        text,
        '        if (choice == "cloud") {\n            say("\\nCloud saves are not available in the C++ port.");\n        }\n',
        '        if (choice == "cloud") {\n            State loaded_state;\n            if (cloud_menu(nullptr, loaded_state)) {\n                return loaded_state;\n            }\n        }\n',
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

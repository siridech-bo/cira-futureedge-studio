#pragma once

#include <string>
#include <map>
#include <mutex>
#include <ctime>

namespace CiraBlockRuntime {

class AuthManager {
public:
    AuthManager();

    // Set credentials
    void SetCredentials(const std::string& username, const std::string& password);

    // Login and get token
    std::string Login(const std::string& username, const std::string& password);

    // Validate token
    bool ValidateToken(const std::string& token);

    // Logout (invalidate token)
    void Logout(const std::string& token);

    // Check if auth is enabled
    bool IsAuthEnabled() const;

private:
    std::mutex mutex_;
    std::string username_;
    std::string password_hash_;
    std::map<std::string, time_t> active_tokens_;  // token -> expiry timestamp
    bool auth_enabled_;

    // Token management
    std::string GenerateToken();
    std::string HashPassword(const std::string& password);
    void CleanupExpiredTokens();

    static constexpr time_t TOKEN_LIFETIME_SECONDS = 86400;  // 24 hours
};

} // namespace CiraBlockRuntime

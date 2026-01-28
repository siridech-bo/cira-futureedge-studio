#include "auth_manager.hpp"
#include <random>
#include <sstream>
#include <iomanip>
#include <algorithm>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <wincrypt.h>
#else
#include <openssl/sha.h>
#endif

namespace CiraBlockRuntime {

AuthManager::AuthManager()
    : auth_enabled_(false) {
}

void AuthManager::SetCredentials(const std::string& username, const std::string& password) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (username.empty() || password.empty()) {
        auth_enabled_ = false;
        username_.clear();
        password_hash_.clear();
        return;
    }

    username_ = username;
    password_hash_ = HashPassword(password);
    auth_enabled_ = true;
}

std::string AuthManager::Login(const std::string& username, const std::string& password) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (!auth_enabled_) {
        // Auth disabled, return a dummy token
        return "no-auth-required";
    }

    // Verify credentials
    if (username != username_ || HashPassword(password) != password_hash_) {
        return "";  // Invalid credentials
    }

    // Generate new token
    std::string token = GenerateToken();
    active_tokens_[token] = time(nullptr) + TOKEN_LIFETIME_SECONDS;

    CleanupExpiredTokens();

    return token;
}

bool AuthManager::ValidateToken(const std::string& token) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (!auth_enabled_) {
        return true;  // Auth disabled, all requests allowed
    }

    auto it = active_tokens_.find(token);
    if (it == active_tokens_.end()) {
        return false;  // Token not found
    }

    if (it->second < time(nullptr)) {
        active_tokens_.erase(it);  // Token expired
        return false;
    }

    return true;
}

void AuthManager::Logout(const std::string& token) {
    std::lock_guard<std::mutex> lock(mutex_);
    active_tokens_.erase(token);
}

bool AuthManager::IsAuthEnabled() const {
    return auth_enabled_;
}

std::string AuthManager::GenerateToken() {
    // Generate random token (32 hex characters)
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 255);

    std::ostringstream oss;
    for (int i = 0; i < 16; ++i) {
        oss << std::hex << std::setw(2) << std::setfill('0') << dis(gen);
    }

    return oss.str();
}

std::string AuthManager::HashPassword(const std::string& password) {
    // Simple SHA256 hash (for demonstration - in production use bcrypt/scrypt)
#ifdef _WIN32
    // Windows: Use CryptoAPI for SHA256
    HCRYPTPROV hProv = 0;
    HCRYPTHASH hHash = 0;
    BYTE hash[32];
    DWORD hashLen = 32;

    if (!CryptAcquireContext(&hProv, NULL, NULL, PROV_RSA_AES, CRYPT_VERIFYCONTEXT)) {
        return "";
    }

    if (!CryptCreateHash(hProv, CALG_SHA_256, 0, 0, &hHash)) {
        CryptReleaseContext(hProv, 0);
        return "";
    }

    if (!CryptHashData(hHash, (const BYTE*)password.c_str(), password.length(), 0)) {
        CryptDestroyHash(hHash);
        CryptReleaseContext(hProv, 0);
        return "";
    }

    if (!CryptGetHashParam(hHash, HP_HASHVAL, hash, &hashLen, 0)) {
        CryptDestroyHash(hHash);
        CryptReleaseContext(hProv, 0);
        return "";
    }

    CryptDestroyHash(hHash);
    CryptReleaseContext(hProv, 0);

    std::ostringstream oss;
    for (DWORD i = 0; i < hashLen; ++i) {
        oss << std::hex << std::setw(2) << std::setfill('0') << (int)hash[i];
    }

    return oss.str();
#else
    // Linux: Use OpenSSL SHA256
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256((const unsigned char*)password.c_str(), password.length(), hash);

    std::ostringstream oss;
    for (int i = 0; i < SHA256_DIGEST_LENGTH; ++i) {
        oss << std::hex << std::setw(2) << std::setfill('0') << (int)hash[i];
    }

    return oss.str();
#endif
}

void AuthManager::CleanupExpiredTokens() {
    time_t now = time(nullptr);

    auto it = active_tokens_.begin();
    while (it != active_tokens_.end()) {
        if (it->second < now) {
            it = active_tokens_.erase(it);
        } else {
            ++it;
        }
    }
}

} // namespace CiraBlockRuntime

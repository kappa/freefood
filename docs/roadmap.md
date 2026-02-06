# FreeFood Roadmap

This document outlines future features, enhancements, and considerations for the FreeFood console client, beyond the initial v1.0 release.

## Core Social Features
- **Attachments Upload**: Support for attaching images and files when creating or editing posts.
- **Bookmarks & Saves**: Ability to view and manage bookmarked/saved posts.
- **Advanced Search**: A dedicated search form/UI for building complex queries with operators.
- **User Profile Management**: Support for editing the user's own profile (bio, screen name, etc.).
- **Group Management**: Administrative functions for group owners (creating groups, managing members).

## UI & UX Enhancements
- **Real-time Updates**: Integration with FreeFeed WebSockets for live feed and notification updates without manual refresh.
- **Auto-refresh**: Optional background polling for users who prefer it over manual F5.
- **Enhanced Media Support**:
    - Inline image previews (using terminal graphics protocols like Sixel or Kitty).
    - Thumbnail display in the post view.
    - Basic audio/video playback capabilities via external integration.
- **Customization**:
    - Keyboard shortcut customization.
    - Support for custom color themes.
- **Mouse Support**: Enabling mouse interaction for navigation and buttons (supported by Textual).

## Architecture & Performance
- **Offline Mode**: Local caching of content for viewing feeds without an active internet connection.
- **Improved Performance**: Optimizing denormalization and rendering for very long timelines.

## Packaging & Distribution
- **Native Package Managers**: Support for Homebrew (macOS), winget (Windows), and AUR (Arch Linux).
- **Advanced Linux Formats**: AppImage or Flatpak support.
- **Native Installers**: `.dmg` for macOS and proper Windows installers.
- **Auto-update**: Integrated mechanism to check for and install new versions.
- **Code Signing**: Proper signing for macOS and Windows executables to avoid OS warnings.

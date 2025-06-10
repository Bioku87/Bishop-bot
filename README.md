# Bishop Bot

A versatile Discord bot for tabletop RPG sessions with voice transcription, character management, and audio playback capabilities.

**Last Updated:** May 31, 2025

## Features

- **Voice Transcription**: Automatically transcribe voice chat sessions into text
- **Character Management**: Create and manage D&D characters
- **Audio Controls**: Play music and audio clips during your sessions
- **Soundboard**: Organized audio clips for quick access during gameplay
- **Control Panel**: GUI interface for managing all bot features

## Setup Instructions

1. Install Python 3.8 or higher
2. Run `install_voice_deps.bat` to install voice recognition dependencies
3. Create a `.env` file with your Discord token (see `.env.example`)
4. Run `verify_setup.py` to make sure everything is installed correctly
5. Use `run.bat` to start the bot

## Voice Commands

| Command | Description |
|---------|-------------|
| /activate_voice | Connect to your voice channel |
| /deactivate | Disconnect from voice channel |
| /listen | Start transcribing voice to text |
| /stopsession | Stop the current transcription session |
| /exporttranscript | Export the transcript to a file |

## Character Commands

| Command | Description |
|---------|-------------|
| /register | Register a new character |
| /mycharacter | View your character details |
| /update_character | Update your character information |

## Music Commands

| Command | Description |
|---------|-------------|
| /play | Play audio from a URL |
| /stop_music | Stop music playback |
| /skip | Skip to next track |
| /queue | Show the current music queue |
| /volume | Set the music volume |

## Admin Commands

| Command | Description |
|---------|-------------|
| /fix_voice | Fix voice connection tracking |
| /test_voice | Test voice connections |

## Control Window

The bot includes a graphical control window with the following tabs:

- **Dashboard**: View bot status and active transcription
- **Commands**: Execute Discord commands directly
- **Audio**: Manage audio files and soundboard
- **Characters**: Create and edit character profiles
- **Transcripts**: View and export past transcription sessions

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b new-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin new-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Discord.py team for the Discord API wrapper
- FFmpeg developers for audio processing capabilities
- All contributors to the project
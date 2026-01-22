"""OS notification support for KifDiff."""

def show_notification(title, message, notification_type="info"):
    """Show OS notification."""
    try:
        import platform
        system = platform.system()
        
        if system == "Darwin":  # macOS
            # Use osascript for macOS notifications
            import subprocess
            # Map notification type to sound name
            sound_map = {
                "success": "Glass",
                "error": "Basso", 
                "warning": "Ping",
                "info": "Pop"
            }
            sound = sound_map.get(notification_type, "Pop")
            
            cmd = [
                'osascript', '-e',
                f'display notification "{message}" with title "{title}" sound name "{sound}"'
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
        elif system == "Linux":
            # Use notify-send for Linux
            import subprocess
            urgency_map = {
                "success": "normal",
                "error": "critical",
                "warning": "normal", 
                "info": "low"
            }
            urgency = urgency_map.get(notification_type, "normal")
            
            cmd = ['notify-send', '-u', urgency, title, message]
            subprocess.run(cmd, check=True)
            
        elif system == "Windows":
            # Try to use win10toast for Windows
            try:
                from win10toast import ToastNotifier
                toast = ToastNotifier()
                toast.show_toast(title, message, duration=3, threaded=True)
            except ImportError:
                # Fallback: no notification on Windows without win10toast
                pass
                
    except Exception as e:
        # Silently fail if notifications don't work
        from .output import print_warning
        print_warning(f"Could not show notification: {e}")

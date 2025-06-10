# Simple theme for Bishop Bot
# Last updated: 2025-06-01 05:36:41

# Create the theme
namespace eval ttk::theme::sunvalley {
    ttk::style theme create sunvalley -parent default -settings {
        # Configure the basic style elements
        ttk::style configure . \
            -background "#2b2b2b" \
            -foreground "#ffffff" \
            -troughcolor "#4a4a4a" \
            -focuscolor "#0078d7" \
            -selectbackground "#0078d7" \
            -selectforeground "#ffffff" \
            -fieldbackground "#363636" \
            -borderwidth 1 \
            -relief flat

        # Configure specific elements
        ttk::style map . \
            -foreground [list disabled "#a0a0a0"] \
            -background [list disabled "#383838"]
        
        # Button style
        ttk::style configure TButton \
            -padding {5 2} \
            -background "#3c3c3c" \
            -foreground "#ffffff"
        
        ttk::style map TButton \
            -background [list active "#4f4f4f" pressed "#2b2b2b"]
            
        # Frame style  
        ttk::style configure TFrame -background "#2b2b2b"
            
        # Label style
        ttk::style configure TLabel -background "#2b2b2b" -foreground "#ffffff"
            
        # Entry style
        ttk::style configure TEntry -selectbackground "#0078d7" -fieldbackground "#363636"
            
        # Combobox style
        ttk::style configure TCombobox -selectbackground "#0078d7" -fieldbackground "#363636"
    }
}

# Create a command to set the theme
proc set_theme {mode} {
    if {$mode eq "dark"} {
        ttk::style theme use sunvalley
    } else {
        ttk::style theme use default
    }
}
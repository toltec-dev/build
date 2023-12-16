"""
Built in hooks
"""
__all__ = [
    "patch_rm2fb",
    "strip",
    "reload_oxide_apps",  # Depends on install_lib
    # This hook needs to come after any hooks that may depend on it
    "install_lib",
]

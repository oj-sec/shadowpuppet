#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::time::Duration;
use std::sync::{Arc, Mutex};
use tauri::{Manager, Url}; 
use tauri_plugin_shell::ShellExt;
use reqwest;

fn main() {
    let child_process = Arc::new(Mutex::new(None));
    let child_process_clone = child_process.clone();
    
    tauri::Builder::default()
    .plugin(tauri_plugin_fs::init())
    .plugin(tauri_plugin_shell::init())
    .setup(move |app| {
        if let Some(main_window) = app.get_webview_window("main") {
            main_window.hide().expect("Failed to hide main window");
        }

        let server_ready = Arc::new(Mutex::new(false));
        let app_handle = app.app_handle().clone();
        let loading_path = app.path().resolve("resources/loading.html", tauri::path::BaseDirectory::Resource)
            .expect("Failed to resolve loading HTML resource");
        let loading_url = tauri::Url::from_file_path(loading_path)
            .expect("Failed to convert path to URL");
        
        tauri::WebviewWindowBuilder::new(
            app,
            "loading", 
            tauri::WebviewUrl::External(loading_url)
        )
        .title("Loading Application")
        .center()
        .inner_size(400.0, 300.0)
        .resizable(false)
        .decorations(false) 
        .build()
        .expect("Failed to create loading window");
        
        
        let check_handle = app_handle.clone();
        let check_ready = server_ready.clone();
        tauri::async_runtime::spawn(async move {
            tokio::time::sleep(Duration::from_secs(2)).await;
            for _ in 0..60 {
                if *check_ready.lock().unwrap() {
                    break; 
                }
                
                match reqwest::get("http://localhost:8000").await {
                    Ok(_) => {
                        println!("Server is responding to HTTP requests");
                        *check_ready.lock().unwrap() = true;
                        close_loading_and_show_main(check_handle.clone()).await;
                        break; 
                    },
                    Err(e) => {
                        println!("Server not responding yet: {}", e);
                        tokio::time::sleep(Duration::from_secs(1)).await;
                    }
                }
            }
        });
        
        tauri::async_runtime::spawn(async move {
            let app_handle = app_handle.clone();
            
            let sidecar_command = app_handle.shell().sidecar("shadowpuppet-server").unwrap();
            let (mut rx, child) = sidecar_command
            .spawn()
            .expect("Failed to spawn server sidecar");
            
            *child_process.lock().unwrap() = Some(child);
            
            while let Some(event) = rx.recv().await {
                match event {
                    tauri_plugin_shell::process::CommandEvent::Stdout(line_bytes) => {
                        let line = String::from_utf8_lossy(&line_bytes);
                        println!("Server stdout: {}", line);
                        
                        if !*server_ready.lock().unwrap()
                        && (line.contains("Application startup complete")
                        || line.contains("Uvicorn running")
                        || line.contains("Listening on")
                        || line.contains("Started server process"))
                        {
                            *server_ready.lock().unwrap() = true;
                            println!("Server is ready based on log output");
                            close_loading_and_show_main(app_handle.clone()).await;
                        }
                    }
                    tauri_plugin_shell::process::CommandEvent::Stderr(line_bytes) => {
                        let line = String::from_utf8_lossy(&line_bytes);
                        println!("Server stderr: {}", line);
                        
                        if !*server_ready.lock().unwrap()
                        && (line.contains("Application startup complete")
                        || line.contains("Uvicorn running")
                        || line.contains("Listening on")
                        || line.contains("Started server process"))
                        {
                            *server_ready.lock().unwrap() = true;
                            println!("Server is ready based on stderr output");
                            close_loading_and_show_main(app_handle.clone()).await;
                        }
                    }
                    tauri_plugin_shell::process::CommandEvent::Error(err) => {
                        eprintln!("Server error: {}", err);
                    }
                    tauri_plugin_shell::process::CommandEvent::Terminated(payload) => {
                        println!("Server process terminated with code: {:?}", payload.code);
                    },
                    _ => {
                        println!("Unhandled command event type");
                    }
                }
            }
        });
        
        let main_window = app.get_webview_window("main").expect("Failed to get main window");
        let app_handle2 = app.app_handle().clone();
        
        main_window.on_window_event(move |event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                println!("Window close requested, sending shutdown signal to server...");
                
                match reqwest::blocking::get("http://localhost:8000/shutdown") {
                    Ok(response) => {
                        if response.status().is_success() {
                            println!("Successfully sent shutdown request to server");
                        } else {
                            println!("Server responded with non-success status: {}", response.status());
                        }
                    },
                    Err(e) => {
                        eprintln!("Failed to send shutdown request: {}", e);
                    }
                }
                
                std::thread::sleep(std::time::Duration::from_millis(1000));
                
                if let Some(child) = child_process_clone.lock().unwrap().take() {
                    println!("Additionally attempting standard process termination");
                    let _ = child.kill(); 
                }
                
                app_handle2.exit(0);
            }
        });
        
        Ok(())
    })
    .run(tauri::generate_context!())
    .expect("Error running Tauri application");
}

async fn close_loading_and_show_main(app_handle: tauri::AppHandle) {
    tokio::time::sleep(Duration::from_millis(500)).await;
    
    if let Some(loading_window) = app_handle.get_webview_window("loading") {
        println!("Closing loading window");
        let _ = loading_window.close();
    }
    
    if let Some(main_window) = app_handle.get_webview_window("main") {
        let url = Url::parse("http://localhost:8000").expect("Invalid URL");
        let _ = main_window.navigate(url);

        tokio::time::sleep(Duration::from_millis(400)).await;
        
        let _ = main_window.show();
        println!("Main window shown");
    } else {
        println!("Main window not found when trying to show");
    }
}
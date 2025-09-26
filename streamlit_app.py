import os
import io
import time
import sys
from pathlib import Path
from typing import List, Optional

# Add current directory to Python path for proper imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

import streamlit as st

# Import from new 4-layer architecture
from logic.orchestration.engine import PMAnalysisEngine
from logic.orchestration.config_manager import ConfigManager
from logic.models.models import ProcessingResult
from ui.common.exceptions import ValidationError
from service.avatar import AvatarService

APP_TITLE = "Minimal PM‑Assistent (Streamlit UI)"

def save_uploaded_files(files, dest_dir: Path) -> list[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for f in files or []:
        # Keep original filename; ensure uniqueness
        target = dest_dir / f.name
        # If duplicate, add suffix
        i = 1
        while target.exists():
            target = dest_dir / f"{target.stem}_{i}{target.suffix}"
            i += 1
        with open(target, "wb") as out:
            out.write(f.getbuffer())
        saved.append(target)
    return saved

def run_engine(engine: PMAnalysisEngine, mode: Optional[str], project_path: Path, output_formats: Optional[list[str]]):
    # Normalize parameters for engine.run()
    mode_value = mode if mode not in (None, "", "auto") else None
    formats = output_formats if output_formats else None
    return engine.run(mode=mode_value, project_path=str(project_path), output_formats=formats)

def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)
    st.caption("Grafische Oberfläche als Ersatz für die CLI `main.py` – wählt Modus, lädt Dateien und generiert Berichte.")

    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    # Initialize avatar service
    avatar_service = AvatarService(config)
    
    # Sidebar: configuration & status
    with st.sidebar:
        st.header("Konfiguration")
        mode = st.selectbox(
            "Modus",
            options=["auto", "document-check", "status-analysis", "learning-module"],
            index=0,
            help="Auto erkennt den Modus anhand der vorhandenen Dateien.",
        )
        st.write("**Ausgabeformate**")
        fmt_md = st.checkbox("Markdown", value=True)
        fmt_xlsx = st.checkbox("Excel", value=False)
        # Note: "console" format is not supported by the engine, so we don't include it as an option
        output_formats = [f for f, on in (("markdown", fmt_md), ("excel", fmt_xlsx)) if on]

        st.divider()
        st.subheader("Engine‑Status")
        try:
            # Try to create engine with explicit error handling
            @st.cache_resource
            def create_engine():
                try:
                    from logic.orchestration.engine import PMAnalysisEngine
                    engine = PMAnalysisEngine()
                    return engine, None
                except Exception as e:
                    return None, str(e)
            
            engine, engine_error = create_engine()
            
            if engine_error:
                st.error(f"Engine initialization failed: {engine_error}")
                st.write("**Debug Info:**")
                st.code(f"Error: {engine_error}")
                return
            elif engine is None:
                st.error("Engine is None - unknown initialization error")
                return
            else:
                status = engine.get_engine_status()
                proc_info = engine.get_processor_info()
                st.success(f"Engine initialized with {len(engine.processors)} processors")
                st.json(status)
                if proc_info:
                    with st.expander("Verfügbare Prozessoren"):
                        st.json(proc_info)
        except Exception as e:
            st.error(f"Fehler beim Initialisieren der Engine: {e}")
            st.exception(e)
            return

    # Main content area with avatar
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Projektdateien")
        st.write("Laden Sie die relevanten Dateien hoch (z. B. PDF/DOCX, MPP, XLSX). Alternativ können Sie einen existierenden Projektordner angeben.")
        upload = st.file_uploader(
            "Dateien hochladen",
            accept_multiple_files=True,
            help="Mehrfachauswahl möglich. Die Dateien werden in einen temporären Projektordner kopiert."
        )

        default_project_dir = Path("uploaded_project")
        project_dir = st.text_input("Projektpfad (optional)", value=str(default_project_dir))

        if st.button("Analyse starten", type="primary"):
            project_path = Path(project_dir).expanduser().resolve()
            saved = save_uploaded_files(upload, project_path)

            with st.status("Starte Analyse …", expanded=True) as status_box:
                try:
                    # Get the cached engine
                    engine, engine_error = create_engine()
                    
                    if engine_error or engine is None:
                        st.error(f"Engine nicht verfügbar: {engine_error or 'Unknown error'}")
                        status_box.update(label="Engine-Fehler", state="error")
                        return
                    
                    st.write(f"✓ Engine bereit mit {len(engine.processors)} Prozessoren")
                    
                    t0 = time.time()
                    result: ProcessingResult = run_engine(engine, mode, project_path, output_formats)
                    dt = time.time() - t0
                    st.write(f"⏱️ Dauer: {dt:.2f} s")

                    if not result.success:
                        st.error(f"Analyse fehlgeschlagen ({result.operation}).")
                        if hasattr(result, 'errors') and result.errors:
                            st.write("**Fehlerdetails:**")
                            for error in result.errors:
                                st.code(error)
                        status_box.update(label="Analyse fehlgeschlagen", state="error")
                        return
                    else:
                        st.success(f"Analyse abgeschlossen: {result.operation}")
                        
                        # Show warnings if any
                        if hasattr(result, 'warnings') and result.warnings:
                            with st.expander(f"Warnungen ({len(result.warnings)})"):
                                for warning in result.warnings:
                                    st.warning(warning)

                    # Show summary
                    st.write("### Zusammenfassung")
                    st.json({
                        "operation": result.operation,
                        "processing_time_seconds": getattr(result, "processing_time_seconds", None),
                        "messages": getattr(result, "messages", None)
                    })

                    # If markdown/excel reporters wrote files, offer downloads from configured output directory
                    output_section = st.container()
                    with output_section:
                        downloads = []
                        
                        # Check both configured output directory and default reports directory
                        output_dirs = [Path("reports"), Path("outputs")]
                        
                        for out_dir in output_dirs:
                            if out_dir.exists():
                                for p in sorted(out_dir.glob("*")):
                                    if p.is_file() and p.name.endswith(('.md', '.xlsx', '.pdf', '.txt')):
                                        downloads.append(p)

                        if downloads:
                            st.write("### Generierte Dateien")
                            for p in downloads:
                                with open(p, "rb") as fh:
                                    st.download_button(
                                        label=f"Download {p.name}",
                                        data=fh.read(),
                                        file_name=p.name,
                                        mime="application/octet-stream",
                                    )
                        elif "markdown" in output_formats or "excel" in output_formats:
                            st.info("Es wurden noch keine Ausgabedateien im Ordner reports/ oder outputs/ gefunden. Prüfen Sie Reporter‑Konfiguration.")

                    status_box.update(label="Fertig", state="complete")
                except ValidationError as ve:
                    status_box.update(label="Eingabefehler", state="error")
                    st.error(str(ve))
                except Exception as e:
                    status_box.update(label="Fehler", state="error")
                    st.exception(e)
    
    with col2:
        st.subheader("Assistent")
        if avatar_service.is_enabled():
            # Display avatar
            st.markdown(avatar_service.get_avatar_html(300, 300), unsafe_allow_html=True)
            
            # Text input for user to ask the avatar
            user_question = st.text_input("Frage stellen:", placeholder="Stellen Sie eine Frage zum Projekt...")
            
            if user_question and st.button("Frage senden"):
                with st.spinner("Avatar denkt nach..."):
                    # In a real implementation, this would call the avatar service
                    # For now, we'll just show a placeholder response
                    st.info(f"Ihre Frage: {user_question}")
                    st.success("Vielen Dank für Ihre Frage. In einer vollständigen Implementierung würde der Avatar Ihnen jetzt antworten.")
        else:
            st.info("Avatar-Funktionalität ist nicht konfiguriert. Fügen Sie die API-Schlüssel in der config.yaml hinzu, um den Avatar zu aktivieren.")

    st.caption("Hinweis: Diese UI ruft intern `PMAnalysisEngine.run(mode, project_path, output_formats)` auf.")

if __name__ == "__main__":
    main()
// app/static/app.js
// Lógica principal de Scraping

const urlForm = document.getElementById("urlForm");
const fileForm = document.getElementById("fileForm");

const table = document.getElementById("leadsTable");
const statusBox = document.getElementById("status");
const counter = document.getElementById("counter");

let selectedLeadId = null;

// =============================
// ANÁLISIS MANUAL DE URLS
// =============================

urlForm?.addEventListener("submit", async (event) => {
    event.preventDefault();

    setStatus("Analizando URLs públicas...");

    const urlsText = getValue("urlsInput");

    const urls = urlsText
        .split("\n")
        .map((url) => url.trim())
        .filter((url) => url.length > 0);

    if (urls.length === 0) {
        setStatus("Introduce al menos una URL.");
        return;
    }

    if (urls.length > 100) {
        setStatus("El límite máximo es de 100 URLs por análisis.");
        return;
    }

    const payload = {
        urls: urls,
        sector: getValue("urlSector"),
        city: getValue("urlCity"),
        country: getValue("urlCountry")
    };

    showLoading(
        "Analizando URLs públicas",
        "Estamos revisando las webs y detectando datos comerciales."
    );

    try {
        const response = await fetch("/api/analyze-urls", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error("Error al analizar URLs.");
        }

        const result = await response.json();

        setStatus(
            `URLs analizadas. Leads creados/actualizados: ${result.created}. Errores: ${result.errors.length}.`
        );

        renderAnalysisResult({
            ...result,
            total_urls_detected: urls.length
        });

        await loadLeads();

    } catch (error) {
        setStatus(error.message);
    } finally {
        hideLoading();
    }
});

// =============================
// IMPORTACIÓN DESDE ARCHIVO TXT/CSV
// =============================

fileForm?.addEventListener("submit", async (event) => {
    event.preventDefault();

    setStatus("Importando archivo y analizando URLs...");

    const fileInput = document.getElementById("urlsFile");

    if (!fileInput.files || fileInput.files.length === 0) {
        setStatus("Selecciona un archivo TXT o CSV.");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("sector", getValue("fileSector"));
    formData.append("city", getValue("fileCity"));
    formData.append("country", getValue("fileCountry"));

    showLoading(
        "Analizando archivo",
        "Estamos leyendo el archivo, detectando URLs y generando leads."
    );

    try {
        const response = await fetch("/api/analyze-file", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error("Error al importar archivo.");
        }

        const result = await response.json();

        setStatus(
            `Archivo analizado. URLs detectadas: ${result.total_urls_detected}. Leads creados/actualizados: ${result.created}. Errores: ${result.errors.length}.`
        );

        renderAnalysisResult(result);

        await loadLeads();

    } catch (error) {
        setStatus(error.message);
    } finally {
        hideLoading();
    }
});

// =============================
// CARGA Y RENDER DE LEADS
// =============================

async function loadLeads() {
    const sector = getValue("filterSector");
    const city = getValue("filterCity");
    const minScore = getValue("filterScore") || 0;

    const params = new URLSearchParams();

    if (sector) {
        params.append("sector", sector);
    }

    if (city) {
        params.append("city", city);
    }

    params.append("min_score", minScore);

    try {
        const response = await fetch(`/api/leads?${params.toString()}`);

        if (!response.ok) {
            throw new Error("Error al cargar leads.");
        }

        const leads = await response.json();

        renderLeads(leads);
        await loadStats();

    } catch (error) {
        setStatus(error.message);
    }
}

function renderLeads(leads) {
    table.innerHTML = "";
    counter.textContent = `${leads.length} leads`;

    if (leads.length === 0) {
        table.innerHTML = `
            <tr>
                <td colspan="8" class="empty">
                    No hay leads todavía. Analiza URLs o importa un archivo para empezar.
                </td>
            </tr>
        `;
        return;
    }

    leads.forEach((lead) => {
        const row = document.createElement("tr");

        const shortNotes = shortenText(lead.notes || "", 65);
        const formattedTags = formatOpportunityTags(lead.opportunity_tags);
        const shortTags = formattedTags === "-" ? "" : shortenText(formattedTags, 55);
        const contact = lead.generic_email || lead.phone || "-";

        row.innerHTML = `
            <td class="company-cell">
                <strong>${escapeHtml(lead.company_name)}</strong>
                <small>${escapeHtml(shortNotes)}</small>
            </td>

            <td>${escapeHtml(lead.sector)}</td>
            <td>${escapeHtml(lead.city)}</td>

            <td>
                ${lead.website ? `<a href="${escapeHtml(lead.website)}" target="_blank">Web</a>` : "-"}
            </td>

            <td class="contact-cell">${escapeHtml(contact)}</td>

            <td class="score-cell">
                <span class="score ${getScoreClass(lead.lead_score)}">
                    ${lead.lead_score}
                </span>
                <small>${getLeadQuality(lead.lead_score)}</small>
            </td>

            <td class="opportunity-cell">
                <span class="opportunity ${getOpportunityClass(lead.opportunity_score || 0)}">
                    ${getOpportunityLabel(lead.opportunity_score || 0)}
                </span>
                <small>${escapeHtml(shortTags)}</small>
            </td>

            <td class="row-actions">
                <button onclick="openLeadDetail(${lead.id})">Detalle</button>
                <button onclick="enrichLead(${lead.id})">Enriquecer</button>
                <button class="danger small" onclick="deleteLead(${lead.id})">Eliminar</button>
            </td>
        `;

        table.appendChild(row);
    });
}

// =============================
// ACCIONES SOBRE LEADS
// =============================

async function enrichLead(id) {
    setStatus("Enriqueciendo lead...");

    try {
        const response = await fetch(`/api/leads/${id}/enrich`, {
            method: "POST"
        });

        if (!response.ok) {
            throw new Error("Error al enriquecer lead.");
        }

        setStatus("Lead enriquecido correctamente.");
        await loadLeads();

    } catch (error) {
        setStatus(error.message);
    }
}

async function deleteLead(id) {
    if (!confirm("¿Eliminar este lead?")) {
        return;
    }

    try {
        const response = await fetch(`/api/leads/${id}`, {
            method: "DELETE"
        });

        if (!response.ok) {
            throw new Error("Error al eliminar lead.");
        }

        setStatus("Lead eliminado.");
        await loadLeads();

    } catch (error) {
        setStatus(error.message);
    }
}

async function clearLeads() {
    if (!confirm("¿Seguro que quieres eliminar todos los leads?")) {
        return;
    }

    try {
        const response = await fetch("/api/leads", {
            method: "DELETE"
        });

        if (!response.ok) {
            throw new Error("Error al limpiar leads.");
        }

        setStatus("Todos los leads han sido eliminados.");
        await loadLeads();
        await loadStats();

    } catch (error) {
        setStatus(error.message);
    }
}

function resetFilters() {
    setValue("filterSector", "");
    setValue("filterCity", "");
    setValue("filterScore", "0");
    loadLeads();
}

// =============================
// MODAL DE DETALLE
// =============================

async function openLeadDetail(id) {
    selectedLeadId = id;
    setStatus("Cargando detalle del lead...");

    try {
        const response = await fetch(`/api/leads/${id}`);

        if (!response.ok) {
            throw new Error("Error al cargar el detalle del lead.");
        }

        const lead = await response.json();

        renderLeadModal(lead);

        document.getElementById("leadModal").classList.remove("hidden");
        setStatus("Detalle cargado.");

    } catch (error) {
        setStatus(error.message);
    }
}

function closeLeadDetail() {
    document.getElementById("leadModal").classList.add("hidden");
    selectedLeadId = null;
}

function renderLeadModal(lead) {
    document.getElementById("modalCompanyName").textContent = lead.company_name || "-";
    document.getElementById("modalSector").textContent = lead.sector || "-";
    document.getElementById("modalCity").textContent = lead.city || "-";
    document.getElementById("modalScore").textContent = lead.lead_score ?? 0;

    document.getElementById("modalQuality").textContent = getLeadQuality(lead.lead_score || 0);
    document.getElementById("modalOpportunity").textContent = getOpportunityLabel(lead.opportunity_score || 0);

    document.getElementById("modalWebsite").innerHTML = lead.website
        ? `<a href="${escapeHtml(lead.website)}" target="_blank">${escapeHtml(lead.website)}</a>`
        : "-";

    document.getElementById("modalEmail").textContent = lead.generic_email || "-";
    document.getElementById("modalPhone").textContent = lead.phone || "-";

    document.getElementById("modalSocialLinks").innerHTML = formatLinks(lead.social_links);
    document.getElementById("modalTags").textContent = formatOpportunityTags(lead.opportunity_tags);
    document.getElementById("modalNotes").textContent = lead.notes || "-";

    document.getElementById("modalSourceUrl").innerHTML = lead.source_url
        ? `<a href="${escapeHtml(lead.source_url)}" target="_blank">${escapeHtml(lead.source_url)}</a>`
        : "-";

    document.getElementById("modalSourceType").textContent = lead.source_type || "-";
}

async function enrichSelectedLead() {
    if (!selectedLeadId) {
        return;
    }

    await enrichLead(selectedLeadId);
    await openLeadDetail(selectedLeadId);
}

async function deleteSelectedLead() {
    if (!selectedLeadId) {
        return;
    }

    const idToDelete = selectedLeadId;

    closeLeadDetail();
    await deleteLead(idToDelete);
}

// =============================
// RESULTADO DEL ANÁLISIS
// =============================

function renderAnalysisResult(result) {
    const resultCard = document.getElementById("analysisResultCard");
    const totalUrls = document.getElementById("resultTotalUrls");
    const created = document.getElementById("resultCreated");
    const errors = document.getElementById("resultErrors");
    const errorsBox = document.getElementById("errorsBox");
    const errorsList = document.getElementById("errorsList");

    if (!resultCard || !totalUrls || !created || !errors) {
        return;
    }

    resultCard.classList.remove("hidden");

    const totalDetected =
        result.total_urls_detected ??
        result.total_urls ??
        result.leads?.length ??
        0;

    totalUrls.textContent = totalDetected;
    created.textContent = result.created ?? 0;
    errors.textContent = result.errors?.length ?? 0;

    if (!errorsBox || !errorsList) {
        return;
    }

    errorsList.innerHTML = "";

    if (result.errors && result.errors.length > 0) {
        errorsBox.classList.remove("hidden");

        result.errors.forEach((item) => {
            const li = document.createElement("li");

            li.innerHTML = `
                <strong>${escapeHtml(item.url || "URL desconocida")}</strong>
                <span>${escapeHtml(item.error || "Error desconocido")}</span>
            `;

            errorsList.appendChild(li);
        });
    } else {
        errorsBox.classList.add("hidden");
    }
}

// =============================
// ESTADÍSTICAS
// =============================

async function loadStats() {
    try {
        const response = await fetch("/api/stats");

        if (!response.ok) {
            throw new Error("Error al cargar estadísticas.");
        }

        const stats = await response.json();

        document.getElementById("statTotal").textContent = stats.total_leads ?? 0;
        document.getElementById("statAverage").textContent = stats.average_score ?? 0;
        document.getElementById("statCities").textContent = Object.keys(stats.cities || {}).length;
        document.getElementById("statSectors").textContent = Object.keys(stats.sectors || {}).length;

    } catch (error) {
        console.error("Error cargando estadísticas:", error);
    }
}

// =============================
// LOADING OVERLAY
// =============================

function showLoading(title = "Procesando...", text = "La herramienta está trabajando.") {
    const overlay = document.getElementById("loadingOverlay");
    const titleElement = document.getElementById("loadingTitle");
    const textElement = document.getElementById("loadingText");

    if (!overlay || !titleElement || !textElement) {
        return;
    }

    titleElement.textContent = title;
    textElement.textContent = text;
    overlay.classList.remove("hidden");
}

function hideLoading() {
    const overlay = document.getElementById("loadingOverlay");

    if (overlay) {
        overlay.classList.add("hidden");
    }
}

// =============================
// HELPERS
// =============================

function getScoreClass(score) {
    if (score >= 80) {
        return "high";
    }

    if (score >= 50) {
        return "medium";
    }

    return "low";
}

function getLeadQuality(score) {
    if (score >= 80) {
        return "Alta";
    }

    if (score >= 50) {
        return "Media";
    }

    return "Baja";
}

function getOpportunityClass(score) {
    if (score >= 70) {
        return "high";
    }

    if (score >= 40) {
        return "medium";
    }

    return "low";
}

function getOpportunityLabel(score) {
    if (score >= 70) {
        return "Alta";
    }

    if (score >= 40) {
        return "Media";
    }

    return "Baja";
}

function formatOpportunityTags(value) {
    if (!value) {
        return "-";
    }

    const labels = {
        "sin_web": "Sin web detectada",
        "tiene_web": "Tiene web",
        "sin_email_visible": "Sin email visible",
        "email_visible": "Email visible",
        "sin_telefono_visible": "Sin teléfono visible",
        "telefono_visible": "Teléfono visible",
        "sin_redes_detectadas": "Sin redes detectadas",
        "redes_detectadas": "Redes detectadas",
        "sector_interesante": "Sector interesante",
        "contacto_debil": "Contacto débil",
        "presencia_digital_mejorable": "Presencia digital mejorable"
    };

    return String(value)
        .split(",")
        .map((tag) => tag.trim())
        .filter((tag) => tag.length > 0)
        .map((tag) => labels[tag] || tag)
        .join(", ");
}

function formatLinks(value) {
    if (!value) {
        return "-";
    }

    const links = String(value)
        .split(",")
        .map((item) => item.trim())
        .filter((item) => item.length > 0);

    if (links.length === 0) {
        return "-";
    }

    return links
        .map((link) => `<a href="${escapeHtml(link)}" target="_blank">${escapeHtml(link)}</a>`)
        .join("<br>");
}

function getValue(id) {
    return document.getElementById(id)?.value?.trim() || "";
}

function setValue(id, value) {
    const element = document.getElementById(id);

    if (element) {
        element.value = value;
    }
}

function setStatus(message) {
    if (statusBox) {
        statusBox.textContent = message;
    }
}


function shortenText(value, maxLength = 100) {
    const text = String(value || "");

    if (text.length <= maxLength) {
        return text;
    }

    return text.slice(0, maxLength).trim() + "...";
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

// =============================
// INIT
// =============================

document.addEventListener("DOMContentLoaded", () => {
    loadLeads();
    loadStats();
});
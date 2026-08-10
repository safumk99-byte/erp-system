document.addEventListener("DOMContentLoaded", function () {

    console.log("ATTENDANCE JS LOADED");


    // =========================================================
    // Status Colors
    // =========================================================

    const STATUS_COLORS = {
        Present: "#22c55e",
        Late: "#3b82f6",
        Leave: "#facc15",
        Absent: "#ef4444"
    };


    const STATUS_TEXT_COLORS = {
        Present: "#ffffff",
        Late: "#ffffff",
        Leave: "#000000",
        Absent: "#ffffff"
    };


    const STATUS_ORDER = [
        "Present",
        "Late",
        "Leave",
        "Absent"
    ];


    // =========================================================
    // Apply Box Color
    // =========================================================

    function applyBoxColor(box, status) {

        if (!STATUS_COLORS[status]) {
            status = "Present";
        }

        box.style.setProperty(
            "background-color",
            STATUS_COLORS[status],
            "important"
        );

        box.style.setProperty(
            "color",
            STATUS_TEXT_COLORS[status],
            "important"
        );

        box.style.setProperty(
            "border-color",
            STATUS_COLORS[status],
            "important"
        );

        box.dataset.status = status;


        const studentId =
            box.dataset.id;

        const hiddenInput =
            document.getElementById(
                "status_" + studentId
            );

        if (hiddenInput) {
            hiddenInput.value = status;
        }
    }


    // =========================================================
    // Get Next Status
    // =========================================================

    function getNextStatus(status) {

        let index =
            STATUS_ORDER.indexOf(status);

        if (index === -1) {
            index = 0;
        }

        index++;

        if (index >= STATUS_ORDER.length) {
            index = 0;
        }

        return STATUS_ORDER[index];
    }


    // =========================================================
    // Update Summary
    // =========================================================

    function updateSummary() {

        let present = 0;
        let late = 0;
        let leave = 0;
        let absent = 0;


        document
            .querySelectorAll(".attendance-box")
            .forEach(function (box) {

                const status =
                    box.dataset.status;


                if (status === "Present") {
                    present++;
                }

                else if (status === "Late") {
                    late++;
                }

                else if (status === "Leave") {
                    leave++;
                }

                else if (status === "Absent") {
                    absent++;
                }
            });


        const presentCount =
            document.getElementById(
                "presentCount"
            );

        const lateCount =
            document.getElementById(
                "lateCount"
            );

        const leaveCount =
            document.getElementById(
                "leaveCount"
            );

        const absentCount =
            document.getElementById(
                "absentCount"
            );


        if (presentCount) {
            presentCount.textContent = present;
        }

        if (lateCount) {
            lateCount.textContent = late;
        }

        if (leaveCount) {
            leaveCount.textContent = leave;
        }

        if (absentCount) {
            absentCount.textContent = absent;
        }
    }


    // =========================================================
    // Initialize Existing Boxes
    // =========================================================

    const boxes =
        document.querySelectorAll(
            ".attendance-box"
        );


    console.log(
        "Attendance boxes found:",
        boxes.length
    );


    boxes.forEach(function (box) {

        let status =
            box.dataset.status;


        if (!STATUS_COLORS[status]) {
            status = "Present";
        }


        applyBoxColor(
            box,
            status
        );


        // =====================================================
        // Click
        // =====================================================

        box.addEventListener(
            "click",
            function (event) {

                event.preventDefault();
                event.stopPropagation();


                const currentStatus =
                    box.dataset.status ||
                    "Present";


                const nextStatus =
                    getNextStatus(
                        currentStatus
                    );


                console.log(
                    "Student:",
                    box.dataset.id,
                    "Status:",
                    currentStatus,
                    "→",
                    nextStatus
                );


                applyBoxColor(
                    box,
                    nextStatus
                );


                updateSummary();
            }
        );
    });


    // =========================================================
    // Initial Summary
    // =========================================================

    updateSummary();


    // =========================================================
    // Student Popup
    // =========================================================

    function openPopup(box) {

        const popup =
            document.getElementById(
                "studentPopup"
            );

        if (!popup) {
            return;
        }


        const name =
            box.dataset.name || "-";

        const admission =
            box.dataset.admission || "-";

        const className =
            box.dataset.class || "-";

        const parent =
            box.dataset.parent || "-";

        const phone =
            box.dataset.phone || "-";

        const status =
            box.dataset.status || "Present";

        const photo =
            box.dataset.photo || "";


        const popupName =
            document.getElementById(
                "popupName"
            );

        const popupAdmission =
            document.getElementById(
                "popupAdmission"
            );

        const popupClass =
            document.getElementById(
                "popupClass"
            );

        const popupParent =
            document.getElementById(
                "popupParent"
            );

        const popupPhone =
            document.getElementById(
                "popupPhone"
            );

        const popupStatus =
            document.getElementById(
                "popupStatus"
            );

        const popupPhoto =
            document.getElementById(
                "popupPhoto"
            );


        if (popupName) {
            popupName.textContent = name;
        }

        if (popupAdmission) {
            popupAdmission.textContent =
                admission;
        }

        if (popupClass) {
            popupClass.textContent =
                className;
        }

        if (popupParent) {
            popupParent.textContent =
                parent;
        }

        if (popupPhone) {
            popupPhone.textContent =
                phone;
        }

        if (popupStatus) {

            popupStatus.textContent =
                status;

            popupStatus.style.color =
                STATUS_COLORS[status];
        }


        if (popupPhoto) {

            if (photo) {

                if (
                    photo.startsWith("/") ||
                    photo.startsWith("http://") ||
                    photo.startsWith("https://")
                ) {

                    popupPhoto.src = photo;

                } else {

                    popupPhoto.src =
                        "/uploads/" + photo;
                }

            } else {

                popupPhoto.src =
                    "/static/images/default-avatar.png";
            }
        }


        const viewStudent =
            document.getElementById(
                "viewStudent"
            );


        if (viewStudent) {

            viewStudent.href =
                "/student/" +
                box.dataset.id;
        }


        popup.classList.remove(
            "hidden"
        );
    }


    // =========================================================
    // Popup - Right Click
    // =========================================================

    boxes.forEach(function (box) {

        box.addEventListener(
            "contextmenu",
            function (event) {

                event.preventDefault();

                openPopup(box);
            }
        );
    });


    // =========================================================
    // Close Popup
    // =========================================================

    const closePopup =
        document.getElementById(
            "closePopup"
        );


    if (closePopup) {

        closePopup.addEventListener(
            "click",
            function () {

                const popup =
                    document.getElementById(
                        "studentPopup"
                    );

                if (popup) {
                    popup.classList.add(
                        "hidden"
                    );
                }
            }
        );
    }


    // =========================================================
    // Close Popup - Outside
    // =========================================================

    const popup =
        document.getElementById(
            "studentPopup"
        );


    if (popup) {

        popup.addEventListener(
            "click",
            function (event) {

                if (
                    event.target === popup
                ) {

                    popup.classList.add(
                        "hidden"
                    );
                }
            }
        );
    }


    // =========================================================
    // Escape
    // =========================================================

    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Escape"
            ) {

                const popup =
                    document.getElementById(
                        "studentPopup"
                    );

                if (popup) {

                    popup.classList.add(
                        "hidden"
                    );
                }
            }
        }
    );

});
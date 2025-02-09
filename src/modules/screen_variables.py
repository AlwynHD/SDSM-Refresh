from PyQt5.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, QFrame, QLabel, QFileDialog
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPalette, QColor, QIcon
from ScreenVars import correlation, analyseData

# Define the name of the module for display in the content area
moduleName = "Screen Variables"

class ContentWidget(QWidget):
    """
    A widget to display the Screen Variables screen (UI/UX).
    Includes a buttonBar at the top and a contentArea for displaying details.
    """
    def __init__(self):
        """
        Initialize the Screen Variables screen UI/UX, setting up the layout, buttonBar, and contentArea.
        """
        super().__init__()
        
        # Main layout for the entire widget
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        mainLayout.setSpacing(0)  # No spacing between elements
        self.setLayout(mainLayout)  # Apply the main layout to the widget

        # --- Button Bar ---
        # Layout for the buttonBar at the top of the screen
        buttonBarLayout = QHBoxLayout()
        buttonBarLayout.setSpacing(0)  # No spacing between buttons
        buttonBarLayout.setContentsMargins(0, 0, 0, 0)  # No margins around the layout
        buttonBarLayout.setAlignment(Qt.AlignLeft)  # Align buttons to the left

        # Create placeholder buttons for the buttonBar
        buttonNames = ["Reset", "Analyse", "Correlation", "Scatter", "Settings"]  # Names of the buttons for clarity
        for name in buttonNames:
            button = QPushButton(name)  # Create a button with the given name
            button.setIcon(QIcon("placeholder_icon.png"))  # Placeholder icon
            button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)  # Fixed size policy
            button.sizeHint()  # Set a fixed size for the button
            button.setStyleSheet(
                "border: 1px solid lightgray; background-color: #F0F0F0; text-align: left;"
            )  # Style to match the overall design
            buttonBarLayout.addWidget(button)  # Add the button to the buttonBar layout

        # Frame for the buttonBar
        buttonBarFrame = QFrame()
        buttonBarFrame.setLayout(buttonBarLayout)  # Apply the button layout to the frame
        buttonBarFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        buttonBarFrame.setFixedHeight(50)  # Match height with other UI elements
        buttonBarFrame.setStyleSheet("background-color: #A9A9A9;")  # Dark gray background
        mainLayout.addWidget(buttonBarFrame)  # Add the buttonBar frame to the main layout

        # --- Content Area ---
        # Frame for the contentArea
        titleFrame = QFrame()
        titleFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        titleFrame.setFixedHeight(100)

        # Layout for the contentArea frame
        titleLayout = QVBoxLayout()
        titleLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        titleLayout.setSpacing(0)  # No spacing between elements
        titleFrame.setLayout(titleLayout)  # Apply the layout to the frame

        

        # Set the background color to light gray
        titleFrame.setStyleSheet("background-color: #D3D3D3;")

        # Add the title frame to the main layout
        mainLayout.addWidget(titleFrame)

        contentAreaFrame = QFrame()
        contentAreaFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        contentAreaFrame.setBaseSize(100,100)
        contentAreaFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        # Layout for the contentArea frame
        contentAreaLayout = QHBoxLayout()
        contentAreaLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        contentAreaLayout.setSpacing(0)  # No spacing between elements
        contentAreaFrame.setLayout(contentAreaLayout)  # Apply the layout to the frame

        mainLayout.addWidget(contentAreaFrame)


        #Create selectPredictandFile frame
        selectPredictandFileFrame = QFrame()
        selectPredictandFileFrame.setFrameShape(QFrame.StyledPanel)   
        selectPredictandFileFrame.setFixedSize(200,200)


        #Layout for selectPredictandFile frame
        selectPredictandFileLayout = QVBoxLayout()
        selectPredictandFileLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        selectPredictandFileLayout.setSpacing(0)  # No spacing between elements
        selectPredictandFileLayout.setAlignment(Qt.AlignLeft)
        selectPredictandFileFrame.setStyleSheet("background-color: #D3D3D3;")


        selectPredictandFileFrame.setLayout(selectPredictandFileLayout)
        
        contentAreaLayout.addWidget(selectPredictandFileFrame)

        #Create selectPredictor frame
        selectPredictorsFrame = QFrame()
        selectPredictorsFrame.setFrameShape(QFrame.StyledPanel)   
        selectPredictorsFrame.setFixedSize(200,200)


        #Layout for selectPredictors frame
        selectPredictorsLayout = QVBoxLayout()
        selectPredictorsLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        selectPredictorsLayout.setSpacing(0)  # No spacing between elements
        #selectPredictorsLayout.setAlignment(Qt.AlignLeft)
        selectPredictorsFrame.setStyleSheet("background-color: #D3D3D3;")


        selectPredictorsFrame.setLayout(selectPredictorsLayout)
        
        contentAreaLayout.addWidget(selectPredictorsFrame)
        


        # --- Center Label (Placeholder) ---
        # Label to display the name of the module (Screen Variables)
        moduleLabel = QLabel(moduleName, self)
        moduleLabel.setStyleSheet("font-size: 24px; color: black;")  # Style the label text
        titleLayout.addWidget(moduleLabel)  # Add the label to the contentArea layout

        #File selector button
        selectFileButton = QPushButton("Select predictand")
        selectPredictandFileLayout.addWidget(selectFileButton)

        #Blank frame to allow placement wherever I want
        blankFrame = QFrame()
        blankFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        blankFrame.setBaseSize(QSize(200,200))
        blankFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding) #Allow our blank frame to fill the bottom of the screen

        # Layout for the contentArea frame
        blankLayout = QVBoxLayout()
        blankLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        blankLayout.setSpacing(0)  # No spacing between elements
        blankFrame.setLayout(blankLayout)  # Apply the layout to the frame

        mainLayout.addWidget(blankFrame) #Is a bodge, hopefully figure it out later

        # Add a spacer to ensure content is properly spaced
        
        titleLayout.addStretch()
        contentAreaLayout.addStretch()

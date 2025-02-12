from PyQt5.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, QFrame, QLabel
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPalette, QColor, QIcon

# Define the name of the module for display in the content area
moduleName = "Quality Control"

class ContentWidget(QWidget):
    """
    A widget to display the Quality Control screen (UI/UX).
    Includes a buttonBar at the top and a contentArea for displaying details.
    """
    def __init__(self):
        """
        Initialize the Quality Control screen UI/UX, setting up the layout, buttonBar, and contentArea.
        """
        super().__init__()

        self.setStyleSheet("background-color: #D3D3D3;")

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
        buttonNames = ["Reset","Check File", "Daily Stats", "Outliers", "Settings"]  # Names of the buttons for clarity
        for name in buttonNames:
            button = QPushButton(name)  # Create a button with the given name
            button.setIcon(QIcon("placeholder_icon.png"))  # Placeholder icon
            button.clicked.connect(self.handleMenuButtonClicks)
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

        # --- Content Frames ---
        # Frame for the title
        titleFrame = QFrame()
        titleFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        titleFrame.setFixedHeight(100)

        # Layout for the title frame
        titleLayout = QVBoxLayout()
        titleLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        titleLayout.setSpacing(0)  # No spacing between elements
        titleFrame.setLayout(titleLayout)  # Apply the layout to the frame

        # Set the background color to light gray
        titleFrame.setStyleSheet("background-color: #D3D3D3;")

        # Add the contentArea frame to the main layout
        mainLayout.addWidget(titleFrame)

        #Frame that holds all content
        contentAreaFrame = QFrame()
        contentAreaFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        contentAreaFrame.setBaseSize(600,100)
        contentAreaFrame.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Expanding)

        # Layout for the contentArea frame
        contentAreaLayout = QHBoxLayout()
        contentAreaLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        contentAreaLayout.setSpacing(0)  # No spacing between elements
        contentAreaFrame.setLayout(contentAreaLayout)  # Apply the layout to the frame

        mainLayout.addWidget(contentAreaFrame)

        #Frame which holds Select file, Pettitt test, Threshold, and Outlier (SPTO) frames
        SPTOFrame = QFrame()
        SPTOFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        SPTOFrame.setBaseSize(200,400)
        SPTOFrame.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Expanding)

        # Layout for the contentArea frame
        SPTOLayout = QVBoxLayout()
        SPTOLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        SPTOLayout.setSpacing(0)  # No spacing between elements
        SPTOFrame.setLayout(SPTOLayout)  # Apply the layout to the frame

        contentAreaLayout.addWidget(SPTOFrame)

        #Results frame

        resultsFrame = QFrame()
        resultsFrame.setFrameShape(QFrame.StyledPanel)  # No border around the frame
        resultsFrame.setFixedSize(400,400)


        # Layout for the results frame
        resultsLayout = QVBoxLayout()
        resultsLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        resultsLayout.setSpacing(0)  # No spacing between elements
        resultsFrame.setStyleSheet("background-color: #D3D3D3;")

        resultsFrame.setLayout(resultsLayout)  # Apply the layout to the frame

        contentAreaLayout.addWidget(resultsFrame)

        #Create selectFile frame
        selectFileFrame = QFrame()
        selectFileFrame.setFrameShape(QFrame.StyledPanel)   
        selectFileFrame.setFixedSize(200,100)


        #Layout for selectFile frame
        selectFileLayout = QVBoxLayout()
        selectFileLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        selectFileLayout.setSpacing(0)  # No spacing between elements
        selectFileFrame.setStyleSheet("background-color: #D3D3D3;")


        selectFileFrame.setLayout(selectFileLayout)
        
        SPTOLayout.addWidget(selectFileFrame)

        #Create pettitt frame
        pettittFrame = QFrame()
        pettittFrame.setFrameShape(QFrame.StyledPanel)   
        pettittFrame.setFixedSize(200,100)


        #Layout for pettitt frame
        pettittLayout = QVBoxLayout()
        pettittLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        pettittLayout.setSpacing(0)  # No spacing between elements
        pettittFrame.setStyleSheet("background-color: #D3D3D3;")


        pettittFrame.setLayout(pettittLayout)
        
        SPTOLayout.addWidget(pettittFrame)

        #Create threshold frame
        thresholdFrame = QFrame()
        thresholdFrame.setFrameShape(QFrame.StyledPanel)   
        thresholdFrame.setFixedSize(200,100)


        #Layout for threshold frame
        thresholdLayout = QVBoxLayout()
        thresholdLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        thresholdLayout.setSpacing(0)  # No spacing between elements
        thresholdFrame.setStyleSheet("background-color: #D3D3D3;")


        thresholdFrame.setLayout(thresholdLayout)
        
        SPTOLayout.addWidget(thresholdFrame)

        #Create outliers frame
        outliersFrame = QFrame()
        outliersFrame.setFrameShape(QFrame.StyledPanel)   
        outliersFrame.setFixedSize(200,100)


        #Layout for selectFile frame
        outliersLayout = QVBoxLayout()
        outliersLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        outliersLayout.setSpacing(0)  # No spacing between elements
        outliersFrame.setStyleSheet("background-color: #D3D3D3;")


        outliersFrame.setLayout(outliersLayout)
        
        SPTOLayout.addWidget(outliersFrame)

        


        # ------------ ACTUAL CONTENT ------------
        # --- Center Label (Placeholder) ---
        # Label to display the name of the module (Quality Control)
        moduleLabel = QLabel(moduleName, self)
        moduleLabel.setStyleSheet("font-size: 24px; color: black;")  # Style the label text
        titleLayout.addWidget(moduleLabel)  # Add the label to the contentArea layout


        #Blank frame to allow placement wherever I want, without it everything tries to expand down towards the footer, looks horrible
        blankFrame = QFrame()
        blankFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        blankFrame.setBaseSize(QSize(200,200))
        blankFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding) #Allow our blank frame to fill the bottom of the screen

        # Layout for the blank frame
        blankLayout = QVBoxLayout()
        blankLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        blankLayout.setSpacing(0)  # No spacing between elements
        blankFrame.setLayout(blankLayout)  # Apply the layout to the frame

        mainLayout.addWidget(blankFrame) #Is a bodge, hopefully figure it out later

        # Add a spacer to ensure content is properly spaced
        titleLayout.addStretch()
        contentAreaLayout.addStretch()
    
    def handleMenuButtonClicks(self):
        button = self.sender().text()
        if button == "Check File":
            #https://www.youtube.com/watch?v=QY4KKG4TBFo im keeping this in the comments
            print("https://www.youtube.com/watch?v=QY4KKG4TBFo") #Are easter eggs allowed?
        else:
            print("work in progress, pardon our dust")

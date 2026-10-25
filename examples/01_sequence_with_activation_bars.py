"""
Example 01: Sequence Diagram with Stack-Aware Activation Bars & Alt Fragments
Demonstrates creating a clean UML Sequence Diagram without activation bar collisions.
"""

import sys
import os

# Add parent directory to sys.path to run directly from source
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pd_com_edit import PowerDesignerClient, SequenceDiagramBuilder


def main():
    print("[1/4] Connecting to SAP PowerDesigner...")
    client = PowerDesignerClient()
    client.start(visible=True)

    print("[2/4] Initializing Object-Oriented Model (OOM)...")
    model = client.create_oom(name="Authentication_Flow")
    diag = model.SequenceDiagrams.CreateNew()
    diag.Name = "User Login Verification"

    print("[3/4] Building Lifelines and Messages...")
    builder = SequenceDiagramBuilder(diag)

    # Define lifelines
    builder.add_lifeline("User", is_actor=True)
    builder.add_lifeline("AuthUI")
    builder.add_lifeline("AuthService")
    builder.add_lifeline("TokenProvider")
    builder.add_lifeline("UserDB")

    # Sequence of interactions
    builder.add_message("User", "AuthUI", "inputCredentials(username, pass)", message_type="sync")
    builder.add_message("AuthUI", "AuthService", "authenticate(username, pass)", message_type="sync")
    
    # Internal validation query
    builder.add_message("AuthService", "UserDB", "findUserByUsername(username)", message_type="sync")
    builder.add_message("UserDB", "AuthService", "return UserRecord", message_type="reply")

    # Alt Fragment: Credentials Valid
    builder.add_message("AuthService", "TokenProvider", "generateJwt(user)", message_type="sync")
    builder.add_message("TokenProvider", "AuthService", "return JWT", message_type="reply")
    builder.add_message("AuthService", "AuthUI", "authSuccess(token)", message_type="reply")
    builder.add_message("AuthUI", "User", "displayDashboard()", message_type="reply")

    print("[4/4] Applying Stack-Aware Collision Layout...")
    builder.layout_diagram()

    output_path = os.path.abspath("auth_flow.oom")
    client.save_model(model, output_path)
    print(f"Done! Saved model to: {output_path}")


if __name__ == "__main__":
    main()

from database.db_setup import db


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    scholarship_id = db.Column(
        db.Integer,
        db.ForeignKey("scholarships.id"),
        nullable=False
    )
    document_name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Document {self.document_name}>"